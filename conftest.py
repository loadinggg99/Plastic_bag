"""pytest 全局配置：把 app/ 加入 sys.path，并准备测试用环境变量。

先加载 app/.env、再给缺失的 key 补假值。pydantic-settings 中环境变量优先于
.env，顺序反了会让真实 key 被假值覆盖，联网测试会 401。
"""
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    pass
else:
    load_dotenv(APP_DIR / ".env", override=False)

os.environ.setdefault("DEEPSEEK_API_KEY", "sk-test-dummy")
os.environ.setdefault("TAVILY_API_KEY", "tvly-test-dummy")
