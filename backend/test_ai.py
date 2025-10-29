# test_ai.py
import sys
import os

# 将 core 文件夹加入 Python 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "core"))

from deepseek_client import chat_completion
from config import DEEPSEEK_API_KEY

def main():
    print("==== 测试 Deepseek AI 调用 ====")
    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY 未配置，请检查 .env 和 core/config.py")
        return

    prompt = "你好，我想测试 Deepseek AI 接口。"
    print(f"请求内容: {prompt}")

    reply = chat_completion(prompt)
    print("==== AI 回复 ====")
    print(reply)

if __name__ == "__main__":
    main()
