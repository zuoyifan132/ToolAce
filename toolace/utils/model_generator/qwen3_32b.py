"""
@File   : qwen2d5_7b_instruct.py
@Time   : 2025/05/15 10:57
@Author : yliu.lyndon
@Desc   : None
"""
#%%
import json

import requests
from loguru import logger


def generate(system: str, user: str, **kwargs):
    """
    支持 function calling 的 generate 函数
    
    Args:
        messages: 消息列表
        **kwargs: 可选参数，包括 tools, max_tokens, temperature 等
        
    Returns:
        Tuple[str, str, List[Dict]]: (thinking_content, answer_content, tool_calls)
    """
    # 配置URL
    url = "http://10.200.64.10/10-flashc-openllm/v1/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8"
    }
    # 配置请求体
    body = {
        "model": "qwen3-32b",
        "max_tokens": kwargs.get("max_tokens", 4069),
        "temperature": kwargs.get("temperature", 0),
        "stream": False,
        "chat_template_kwargs": {
            "enable_thinking": True
        },
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    
    # 如果传入了 tools，添加到请求体中
    tools = kwargs.get("tools", [])
    if tools:
        body["tools"] = tools
    
    # 发起POST请求
    response = requests.post(url=url, data=json.dumps(body), headers=headers, timeout=100000)
    # 处理异常请求
    if response.status_code != 200:
        raise Exception("请求失败!", f"请求状态码: {response.status_code}, 应答数据: {response.text}")
    
    # 解析应答数据
    thinking_content, answer_content, tool_calls = "", "", []
    response_data = response.json()
    try:
        message = response_data["choices"][0]["message"]
        # 获取 thinking content（根据实际返回字段调整）
        thinking_content = message.get("reasoning_content", "") or message.get("thinking_content", "")
        # 获取回答内容
        answer_content = message.get("content", "")
        # 获取 tool calls
        tool_calls = message.get("tool_calls", [])
    except Exception as exc:
        if "调用Alice审计服务未通过！" in response_data.get("message", ""):
            raise PermissionError("调用Alice审计服务未通过!", response_data) from exc
        logger.error("请求异常!\n应答数据:\n{}\n异常原因:\n{}", response_data, exc)
    
    return thinking_content, answer_content, tool_calls
    

def stream_generate(system: str, user: str, **kwargs) -> str:
    """
    流式生成函数
    """
    # 配置URL
    url = "http://10.200.64.10/10-flashc-openllm/v1/chat/completions"
    # 配置请求头
    headers = {
        "content-type": "application/json;charset=utf-8",
    }
    # 配置请求体
    payload = {
        "model": "qwen3-32b",
        "max_tokens": kwargs.get("max_tokens", 16384),
        "temperature": kwargs.get("temperature", 0),
        "stream": True,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    # 发起POST请求
    response = requests.post(url=url, json=payload, headers=headers, stream=True)
    # 处理异常请求
    if response.status_code != 200:
        raise Exception("模型推理失败!", f"请求状态码: {response.status_code}", f"响应数据: {response.text}")
    # 解析应答数据
    thinking_field, answer_field = "reasoning_content", "content"
    thinking_flag, answer_flag = False, False
    thinking_content, answer_content = "", ""
    for line in response.iter_lines(decode_unicode=True):
        line: str
        if not line:
            continue
        elif line.startswith("data: "):
            line = line.lstrip("data: ")
        elif "调用Alice审计服务未通过！" in line:
            raise PermissionError("调用Alice审计服务未通过!", line)
        else:
            pass
        try:
            if line == "[DONE]":
                break
            data_blk = json.loads(line)
            delta = data_blk.get("choices", [{}])[0].get("delta", {})
            if thinking_field in delta:
                if not thinking_flag:
                    print("<think>\n", end="", flush=True)
                    thinking_flag = True
                content = delta.get(thinking_field, "")
                thinking_content += content
                print(content, end="", flush=True)
            else:
                if thinking_flag:
                    if thinking_content:
                        print("\n</think>", flush=True)
                    thinking_flag = False
                    if not answer_flag:
                        print("<answer>\n", end="", flush=True)
                        answer_flag = True
                content = delta.get(answer_field, "")
                answer_content += content
                print(content, end="", flush=True)
        except Exception as exc:
            logger.error("流式处理异常!\n应答数据:\n{}\n异常原因:\n{}", line, exc)
    if answer_content:
        print("\n</answer>", flush=True)
    return answer_content, thinking_content



if __name__ == '__main__':
    """"""
    content = generate("", "你是什么模型")
    print(content)

# %%
