"""服务启动入口。

在 app/ 下运行：uv run python -m server.main
等价：uv run uvicorn server:app --reload
"""
import uvicorn

from agent.logger import get_logger
from server import app
from server.config import settings

logger = get_logger("server.main")


def main() -> None:
    logger.info("启动服务：http://%s:%s", settings.host, settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
