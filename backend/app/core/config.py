import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(">>> API Key Loaded:", bool(DEEPSEEK_API_KEY))
