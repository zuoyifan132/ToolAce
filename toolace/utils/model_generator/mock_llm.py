"""
@File   : mock_llm.py
@Time   : 2025/09/17 14:19
@Author : toolace
@Desc   : Mock LLM 模型模拟器，用于测试和开发
"""

import time
import random
from loguru import logger


# Mock响应模板
MOCK_RESPONSES = {
    "api_generation": """
{
  "name": "get_mock_data",
  "description": "获取模拟数据的API接口",
  "parameters": {
    "type": "object",
    "properties": {
      "data_type": {
        "type": "string",
        "description": "数据类型"
      },
      "count": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "description": "数据数量"
      }
    },
    "required": ["data_type"]
  },
  "returns": {
    "type": "object",
    "description": "模拟数据结果"
  }
}
    """,
    "dialog_generation": "我来帮您处理这个请求。让我调用相应的API来获取信息。",
    "verification": "这个对话看起来是合理的，参数设置正确，没有发现明显的问题。",
    "default": "这是一个模拟的LLM响应。在实际使用中，这里会是真实的模型生成内容。"
}


def generate(system: str, user: str, **kwargs) -> str:
    """
    Mock模型生成函数
    
    Args:
        system: 系统提示词
        user: 用户输入
        **kwargs: 其他参数（temperature, max_tokens等）
        
    Returns:
        模拟生成的文本
    """
    # 模拟API调用延迟
    time.sleep(0.1)
    
    temperature = kwargs.get("temperature", 0.7)
    
    # 根据内容选择响应模板
    if "API" in system or "api" in user.lower():
        response = MOCK_RESPONSES["api_generation"]
    elif "对话" in user or "dialog" in user.lower():
        response = MOCK_RESPONSES["dialog_generation"]
    elif "验证" in user or "verify" in user.lower():
        response = MOCK_RESPONSES["verification"]
    else:
        response = MOCK_RESPONSES["default"]
        
    # 根据temperature添加随机性
    if temperature > 0:
        variations = [
            response,
            response + "\n\n[模拟响应变体]",
            response.replace("。", "！")
        ]
        response = random.choice(variations)
        
    logger.debug(f"Mock LLM 生成响应，长度: {len(response)} 字符")
    return response


def stream_generate(system: str, user: str, **kwargs):
    """
    Mock模型流式生成函数
    
    Args:
        system: 系统提示词
        user: 用户输入
        **kwargs: 其他参数
        
    Yields:
        流式生成的文本片段
    """
    # 获取完整响应
    full_response = generate(system, user, **kwargs)
    
    # 逐字符流式输出
    for char in full_response:
        yield char
        time.sleep(0.01)  # 模拟流式延迟
