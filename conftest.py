"""pytest 全局配置。

要点：
1. 把项目根加进 sys.path，保证 `pytest` 和 `python -m pytest` 都能 import app.*。
2. 测试不依赖开发机上真实的 .env：先把 .env 读进 os.environ，再给仍然缺失的
   密钥兜底成假值。

   注意顺序不能反。pydantic-settings 里 **真实环境变量优先级高于 .env**，
   如果先 setdefault 假值，真 key 就会被假 key 盖掉，联网测试会 401。
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    pass
else:
    load_dotenv(PROJECT_ROOT / ".env", override=False)

os.environ.setdefault("DEEPSEEK_API_KEY", "sk-test-dummy")
os.environ.setdefault("TAVILY_API_KEY", "tvly-test-dummy")
