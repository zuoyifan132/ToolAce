"""
@File   : claude3d7.py
@Time   : 2025/03/11 15:45
@Author : yliu.lyndon
@Desc   : None
"""
#%%
import json
import os
import dotenv
import anthropic
from loguru import logger


dotenv.load_dotenv("../../../.env")


def generate(system: str, user: str, **kwargs) -> tuple:
    """
    使用标准Anthropic API调用Claude模型
    
    Args:
        system: 系统提示
        user: 用户消息
        **kwargs: 其他参数，包括api_key, max_tokens, temperature, tools等
    
    Returns:
        tuple: (thinking_content, answer_text, function_calls)
    """
    # 获取API key
    api_key = kwargs.get("api_key") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("API key 未提供。请通过 api_key 参数或 CLAUDE_API_KEY 环境变量设置。")
    
    # 创建Anthropic客户端
    client = anthropic.Anthropic(api_key=api_key)
    
    # 准备消息
    messages = [{"role": "user", "content": user}]
    
    # 准备请求参数
    request_params = {
        "model": kwargs.get("model", "claude-sonnet-4-20250514"),
        "max_tokens": kwargs.get("max_tokens", 16384),
        "temperature": kwargs.get("temperature", 1.0),
        "system": system,
        "messages": messages,
    }
    
    # 添加tools参数（如果有）
    tools = kwargs.get("tools", [])
    if tools:
        request_params["tools"] = tools
    
    try:
        # 调用API
        response = client.messages.create(**request_params)
        
        # 解析响应数据
        thinking_content = ""
        answer_text = ""
        function_calls = []
        
        # 处理thinking（如果模型支持）
        # Claude标准API中thinking通常在response.thinking中
        if hasattr(response, 'thinking') and response.thinking:
            thinking_content = response.thinking
        
        # 处理文本内容和工具调用
        for content_block in response.content:
            if content_block.type == "text":
                answer_text += content_block.text
            elif content_block.type == "tool_use":
                function_calls.append({
                    "name": content_block.name,
                    "parameters": content_block.input
                })
        
        return thinking_content, answer_text, function_calls
        
    except anthropic.APIError as e:
        logger.error(f"Anthropic API 调用失败: {e}")
        raise Exception(f"模型推理失败: {e}")
    except Exception as e:
        logger.error(f"模型推理异常: {e}")
        raise Exception(f"模型推理异常: {e}")


def stream_generate(system: str, user: str, **kwargs) -> str:
    """
    使用标准Anthropic API进行流式调用Claude模型
    
    Args:
        system: 系统提示
        user: 用户消息
        **kwargs: 其他参数，包括api_key, max_tokens, temperature, tools等
    
    Returns:
        str: 流式生成的完整文本内容
    """
    # 获取API key
    api_key = kwargs.get("api_key") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("API key 未提供。请通过 api_key 参数或 CLAUDE_API_KEY 环境变量设置。")
    
    # 创建Anthropic客户端
    client = anthropic.Anthropic(api_key=api_key)
    
    # 准备消息
    messages = [{"role": "user", "content": user}]
    
    # 准备请求参数
    request_params = {
        "model": kwargs.get("model", "claude-sonnet-4-20250514"),
        "max_tokens": kwargs.get("max_tokens", 8192),
        "temperature": kwargs.get("temperature", 0),
        "system": system,
        "messages": messages,
        "stream": True,
    }
    
    # 添加tools参数（如果有）
    tools = kwargs.get("tools", [])
    if tools:
        request_params["tools"] = tools
    
    try:
        # 流式调用API
        answer_content = ""
        answer_flag = False
        
        with client.messages.stream(**request_params) as stream:
            for text in stream.text_stream:
                if not answer_flag:
                    print("<answer>\n", end="", flush=True)
                    answer_flag = True
                answer_content += text
                print(text, end="", flush=True)
        
        if answer_content:
            print("\n</answer>", flush=True)
        
        return answer_content
        
    except anthropic.APIError as e:
        logger.error(f"Anthropic 流式API 调用失败: {e}")
        raise Exception(f"流式请求失败: {e}")
    except Exception as e:
        logger.error(f"流式处理异常: {e}")
        raise Exception(f"流式处理异常: {e}")


if __name__ == "__main__":
    # Function call调用示例
    
    # 定义工具
    tools = [
        {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、纽约等"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "calculate",
            "description": "执行数学计算",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如：2+3*4"
                    }
                },
                "required": ["expression"]
            }
        }
    ]

    # 示例1：天气查询
    print("=== 示例1：天气查询 ===")
    thinking, answer, func_calls = generate(
        system="你是一个有用的助手",
        user="什么事鄂尔多斯定理",
        # tools=tools,
        max_tokens=1024,
        temperature=0.7,
    )
    
    print(f"Thinking: {thinking}")
    print(f"Answer: {answer}")
    print(f"Function Calls: {func_calls}")
    
    # 示例2：数学计算
    print("\n=== 示例2：数学计算 ===")
    thinking, answer, func_calls = generate(
        system="你是一个有帮助的助手，可以查询天气和进行计算。当用户需要计算时，请使用calculate工具。",
        user="请帮我计算 15 * 24 + 100 的结果",
        tools=tools,
        max_tokens=1024,
        temperature=0.3,
    )
    
    print(f"Thinking: {thinking}")
    print(f"Answer: {answer}")
    print(f"Function Calls: {func_calls}")