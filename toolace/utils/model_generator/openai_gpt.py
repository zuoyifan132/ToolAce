"""
@File   : openai_gpt.py
@Time   : 2025/09/17 14:19
@Author : toolace
@Desc   : OpenAI GPT 模型调用接口
"""

import os
from loguru import logger

try:
    import openai
except ImportError:
    openai = None


def generate(system: str, user: str, **kwargs) -> str:
    """
    OpenAI GPT 模型生成函数
    
    Args:
        system: 系统提示词
        user: 用户输入
        **kwargs: 其他参数（temperature, max_tokens, model_name, api_key等）
        
    Returns:
        生成的文本
    """
    if openai is None:
        raise ImportError("OpenAI package not installed. Please install with: pip install openai")
    
    # 获取配置参数
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in kwargs or environment variables")
    
    model_name = kwargs.get("model_name", "gpt-3.5-turbo")
    temperature = kwargs.get("temperature", 0.7)
    max_tokens = kwargs.get("max_tokens", 1024)
    
    # 创建客户端
    client = openai.OpenAI(api_key=api_key)
    
    # 准备消息
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    
    logger.debug(f"调用 OpenAI {model_name} 模型，参数: temperature={temperature}, max_tokens={max_tokens}")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content
        logger.debug(f"OpenAI 模型响应成功，长度: {len(result)} 字符")
        return result
        
    except Exception as e:
        logger.error(f"OpenAI API 调用失败: {e}")
        raise RuntimeError(f"OpenAI API call failed: {e}")


def stream_generate(system: str, user: str, **kwargs):
    """
    OpenAI GPT 模型流式生成函数
    
    Args:
        system: 系统提示词
        user: 用户输入
        **kwargs: 其他参数
        
    Yields:
        流式生成的文本片段
    """
    if openai is None:
        raise ImportError("OpenAI package not installed. Please install with: pip install openai")
    
    # 获取配置参数
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in kwargs or environment variables")
    
    model_name = kwargs.get("model_name", "gpt-3.5-turbo")
    temperature = kwargs.get("temperature", 0.7)
    max_tokens = kwargs.get("max_tokens", 1024)
    
    # 创建客户端
    client = openai.OpenAI(api_key=api_key)
    
    # 准备消息
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    
    logger.debug(f"调用 OpenAI {model_name} 模型流式生成")
    
    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"OpenAI 流式生成失败: {e}")
        raise RuntimeError(f"OpenAI streaming API call failed: {e}")
