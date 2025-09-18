"""
简化的模型管理器

支持动态导入模型模块，采用简单的工厂模式
"""

import sys
import importlib
from typing import Callable, Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed


# 默认模型配置
DEFAULT_MODEL = "qwen3_32b"


def get_model_generator(model_name: str) -> Callable[[str, str, Any], str]:
    """
    获取模型生成器函数
    
    Args:
        model_name: 模型名称，对应 model_generator 目录下的模块名
        
    Returns:
        模型生成函数
    """
    try:
        # 动态导入模型模块
        model_module = importlib.import_module(f"toolace.utils.model_generator.{model_name}")
        logger.info(f"使用 {model_name} 模型进行生成")
        
        # 检查是否有流式生成功能
        if hasattr(model_module, "generate"):
            generate_func = model_module.generate
        elif hasattr(model_module, "stream_generate"):
            generate_func = model_module.stream_generate
        else:
            raise AttributeError(f"模块 `{model_name}` 中不存在 'generate' 或 'stream_generate' 方法!")
            
        return generate_func
        
    except ImportError as e:
        logger.error(f"导入模型模块失败: {model_name}, 错误: {e}")
        # 回退到默认模型
        if model_name != DEFAULT_MODEL:
            logger.warning(f"回退到默认模型: {DEFAULT_MODEL}")
            return get_model_generator(DEFAULT_MODEL)
        else:
            raise ImportError(f"无法导入模型模块: {model_name}")


@retry(
    wait=wait_fixed(10),
    stop=stop_after_attempt(3)
)
def generate(model_key: str, system_prompt: str, user_prompt: str, **kwargs) -> str:
    """
    使用指定模型生成文本（兼容原有接口）
    
    Args:
        model_key: 模型名称（兼容原有的model_key参数）
        system_prompt: 系统提示词
        user_prompt: 用户输入
        **kwargs: 其他参数
        
    Returns:
        生成的文本
    """
    generate_func = get_model_generator(model_key)
    return generate_func(system_prompt, user_prompt, **kwargs)


def stream_generate(model_key: str, system_prompt: str, user_prompt: str, **kwargs):
    """
    使用指定模型进行流式生成（兼容原有接口）
    
    Args:
        model_key: 模型名称（兼容原有的model_key参数）
        system_prompt: 系统提示词
        user_prompt: 用户输入
        **kwargs: 其他参数
        
    Yields:
        生成的文本片段
    """
    generate_func = get_model_generator(model_key)
    
    # 如果是流式函数，直接返回
    if hasattr(generate_func, '__name__') and 'stream' in generate_func.__name__:
        yield from generate_func(system_prompt, user_prompt, **kwargs)
    else:
        # 如果不是流式函数，一次性返回
        result = generate_func(system_prompt, user_prompt, **kwargs)
        yield result
