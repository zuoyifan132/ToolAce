"""
@File   : gemini_2d5_pro.py
@Time   : 2025/08/25 13:34
@Author : yliu.lyndon
@Desc   : None
"""

import json

import requests
from loguru import logger


def generate(system: str, user: str, **kwargs) -> str:
    """
    """
    # 配置URL
    url = "http://10.10.178.25:12239/aigateway/google/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8",
    }
    # 配置请求数据
    payload = {
        "body": {
            "model": "gemini-2.5-pro",
            "maxOutputTokens": kwargs.get("max_tokens", 16384),
            "temperature": kwargs.get("temperature", 0.6),
            "stream": False,
            "contents": [
                {"role": "system", "parts": [{"text": system}]},
                {"role": "user", "parts": [{"text": user}]},
            ],
            "tools": kwargs.get("tools", [{"functionDeclarations": []}]),
        },
        "PKey": "MDlGQTM0RUZFOUYxREY5Njk4MzQyQzcwNDQ1MkIxMDY=",
        "source": "Wind.AI.Insight",
    }
    # 发起POST请求
    response = requests.post(url=url, json=payload, headers=headers)
    # 处理请求失败
    if response.status_code != 200:
        raise Exception("模型推理失败!" f"HTTP状态码: {response.status_code}", f"响应数据: {response.text}")
    # 解析响应数据
    answer_content = ""
    response_data = response.json()
    try:
        content = response_data["body"]["candidates"][0]["content"]["parts"][0]["text"]
        answer_content = content
        function_call = response_data["body"]["candidates"][0]["content"]["parts"][0]["functionCall"]
    except Exception as e:
        if "调用Alice审计服务未通过！" in response_data.get("message", ""):
            raise PermissionError("调用Alice审计服务未通过!", response_data) from e
        logger.error(f"模型推理异常! 异常原因: {e}, 响应数据: {response_data}")
        raise Exception("模型推理异常!", response_data)
    return answer_content


def stream_generate(system: str, user: str, **kwargs) -> str:
    """
    """
    # 配置URL
    url = "http://10.10.178.25:12239/aigateway/google/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8",
    }
    # 配置请求数据
    payload = {
        "body": {
            "model": "gemini-2.5-pro",
            "max_tokens": kwargs.get("max_tokens", 16384),
            "temperature": kwargs.get("temperature", 0.6),
            "stream": True,
            "contents": [
                {"role": "system", "parts": [{"text": system}]},
                {"role": "user", "parts": [{"text": user}]},
            ],
        },
        "PKey": "MDlGQTM0RUZFOUYxREY5Njk4MzQyQzcwNDQ1MkIxMDY=",
        "source": "Wind.AI.Insight",
    }
    # 发起POST请求
    response = requests.post(url=url, json=payload, headers=headers, stream=True)
    # 处理请求失败
    if response.status_code != 200:
        raise Exception("模型推理失败!" f"HTTP状态码: {response.status_code}", f"响应数据: {response.text}")
    # 解析响应数据
    answer_content = ""
    for line in response.iter_lines(decode_unicode=True):
        line: str
        if not line:
            continue
        elif line.startswith("data: "):
            line = line.lstrip("data: ")
        elif "调用Alice审计服务未通过！" in line:
            raise PermissionError("调用Alice审计服务未通过!", line)
        else:
            raise Exception("模型推理异常!", line)
        try:
            data_blk = json.loads(line)
            content = data_blk["candidates"][0]["content"]["parts"][0]["text"]
            answer_content += content
            print(content, end="", flush=True)
        except Exception as e:
            logger.error(f"模型推理异常! 异常原因: {e}, 响应数据: {line}")
    if answer_content:
        print(flush=True)
    return answer_content