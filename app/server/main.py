# app/server/main.py
"""命令行入口。

运行：
    python -m app.server.main
    python app/server/main.py
"""
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]

# 支持直接 `python app/server/main.py`：补上项目根才能 import app.server.xxx
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_DIR))

if importlib.util.find_spec("uvicorn") is None:
    project_python = PROJECT_DIR / ".venv" / "bin" / "python"
    if project_python.is_file() and Path(sys.executable).resolve() != project_python.resolve():
        print(f"当前 Python 缺少 uvicorn，切换到项目环境：{project_python}", file=sys.stderr)
        os.execv(
            str(project_python),
            [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]],
        )

import uvicorn

from app.server import app
from app.server.config import settings


def main() -> None:
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
