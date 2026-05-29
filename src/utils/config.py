"""
集中配置：从 .env 加载 API Key 等敏感信息
"""
import os
from dotenv import load_dotenv

# 加载项目根目录的 .env
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_project_root, ".env"))

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "glm-4.5-air")
XFQ_ROOT = os.getenv("XFQ_ROOT", "C:/Users/Administrator/Desktop/XFQ-Project")
