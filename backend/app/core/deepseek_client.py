import json
import os
from typing import Dict, Iterable, List, Union

import requests
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

if not DEEPSEEK_API_KEY:
    print("⚠️ 没有找到 DEEPSEEK_API_KEY，请检查 .env 文件")


def stream_chat(messages: Iterable[Dict[str, str]]):
    """
    流式调用 DeepSeek API，每次 yield 一个 chunk。
    messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
    """
    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": list(messages),
                "stream": True,
            },
            stream=True,
            timeout=120,
        )
        if not resp.ok:
            raise Exception(f"API 返回错误: {resp.status_code} - {resp.text}")

        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data_str = line.replace("data:", "").strip()
            if data_str == "[DONE]":
                yield {"done": True}
                break
            try:
                json_data = json.loads(data_str)
                delta = json_data["choices"][0]["delta"].get("content")
                if delta:
                    yield {"chunk": delta}
            except Exception as e:
                print("解析流式返回出错:", e)
                continue
    except Exception as e:
        yield {"error": str(e)}


def chat_completion(messages_or_prompt: Union[str, List[Dict[str, str]]]) -> str:
    if isinstance(messages_or_prompt, str):
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": messages_or_prompt}
        ]
    else:
        messages = list(messages_or_prompt)

    result = ""
    for item in stream_chat(messages):
        if "chunk" in item:
            result += item["chunk"]
        elif "error" in item:
            return f"调用模型出错: {item['error']}"
    return result or "模型未返回内容"
