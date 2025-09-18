"""
@File   : claude3d7.py
@Time   : 2025/03/11 15:45
@Author : yliu.lyndon
@Desc   : None
"""
#%%
import json

import requests
from loguru import logger


def generate(system: str, user: str, **kwargs) -> str:
    """
    """
    # 配置URL
    url = "http://10.10.178.25:12239/aigateway/claude/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8",
    }
    # 配置请求数据
    payload = {
        "body": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": kwargs.get("max_tokens", 16384),
            "temperature": kwargs.get("temperature", 1.0),
            "thinking": {
                "type": "enabled",
                "budget_tokens": 8192,
            },
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "tools": kwargs.get("tools", []),
        },
        "PKey": "MDlGQTM0RUZFOUYxREY5Njk4MzQyQzcwNDQ1MkIxMDY=",
        "source": "Wind.AI.Insight",
    }
    # 发起POST请求
    response = requests.post(url=url, json=payload, headers=headers)
    # 处理异常请求
    if response.status_code != 200:
        raise Exception("模型推理失败!", f"HTTP状态码: {response.status_code}", f"响应数据: {response.text}")
    # 解析响应数据
    thinking_block, answer_block, fc_blocks = {}, {}, []
    response_data = response.json()
    try:
        data_blocks = response_data["body"]["content"]
        for data_blk in data_blocks:
            data_blk_type = data_blk.get("type", "")
            if data_blk_type == "thinking":
                thinking_block = data_blk
            elif data_blk_type == "text":
                answer_block = data_blk
            elif data_blk_type == "tool_use":
                fc_blocks.append(data_blk)
            else:
                logger.warning(f"模型推理异常! 异常原因: 数据类型未知! 响应数据: {data_blk}")
    except Exception as e:
        if "调用Alice审计服务未通过！" in response_data.get("message", ""):
            raise PermissionError("调用Alice审计服务未通过!", response_data) from e
        logger.error(f"模型推理异常! 异常原因: {e}, 响应数据: {response_data}")
        raise Exception("模型推理异常!", response_data)
    
    fc_blocks = [
        {
            "name": fc_block["name"],
            "parameters": fc_block["input"]
        }
        for fc_block in fc_blocks
    ]

    return thinking_block["thinking"], answer_block["text"], fc_blocks


def stream_generate(system: str, user: str, **kwargs) -> str:
    """
    """
    # 配置URL
    url = "http://10.10.178.25:12239/aigateway/claude/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8",
        # "wind.sessionid": WIND_SESSION_ID,
    }
    # 配置请求体
    body = {
        "body": {
            "model": "claude-3-7-sonnet-latest",
            "max_tokens": kwargs.get("max_tokens", 8192),
            "temperature": kwargs.get("temperature", 0),
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "tools": kwargs.get("tools", []),
        },
        "PKey": "MDlGQTM0RUZFOUYxREY5Njk4MzQyQzcwNDQ1MkIxMDY=",
        "source": "Wind.AI.Insight",
    }
    # 发起POST请求
    response = requests.post(url=url, data=json.dumps(body), headers=headers, stream=True)
    # 处理异常请求
    if response.status_code != 200:
        raise Exception("请求失败!", f"请求状态码: {response.status_code}, 应答数据: {response.text}")
    # 解析应答数据
    answer_field = "text"
    answer_flag = False
    answer_content = ""
    for line in response.iter_lines(decode_unicode=True):
        line: str
        if not line or line.startswith("event: "):
            continue
        elif line.startswith("data: "):
            line = line.lstrip("data: ")
        elif "调用Alice审计服务未通过！" in line:
            raise PermissionError("调用Alice审计服务未通过!", line)
        else:
            pass
        try:
            data_blk = json.loads(line)
            delta = data_blk.get("delta", {})
            if answer_field in delta:
                if not answer_flag:
                    print("<answer>\n", end="", flush=True)
                    answer_flag = True
                content = delta.get(answer_field, "")
                answer_content += content
                print(content, end="", flush=True)
            else:
                pass
        except Exception as exc:
            logger.error("流式处理异常!\n应答数据:\n{}\n异常原因:\n{}", line, exc)
    if answer_content:
        print("\n</answer>", flush=True)
    return answer_content