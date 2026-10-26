# app/agent/logger.py
"""统一日志配置（参考 project1/agents/logger.py 的写法）。

和参考版的差别：
1. 路径来自 `agent.config.basic_config.LOG_DIR`（= `app/agent/resources/logs/`），
   基于 `__file__` 算绝对路径，不随当前工作目录漂移；
2. 用 `RotatingFileHandler`：单文件 5MB、保留 5 份，长期跑不会把磁盘写爆；
3. 默认同时输出到控制台（`LOG_CONSOLE=0` 可关），本地调试不用再开一个终端 tail；
4. `get_logger("server.query")` 拿子 logger，共用同一套 handler，
   `%(name)s` 能看出日志是哪个模块打的。

用法：
    from agent.logger import get_logger
    logger = get_logger("server.query")
    logger.info("...")
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from agent.config.basic_config import LOG_DIR

LOG_FILE = LOG_DIR / "app.log"
ROOT_LOGGER_NAME = "star_identification"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5


def _console_enabled() -> bool:
    """默认打控制台；`LOG_CONSOLE=0/false/no/off` 时只写文件。"""
    value = os.getenv("LOG_CONSOLE", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def setup_logger(name: str = ROOT_LOGGER_NAME) -> logging.Logger:
    """返回带文件（默认还有控制台）输出的 logger。

    幂等：同名 logger 已经有 handler 就直接复用，不会重复添加——
    不然每调用一次就会多写一遍，日志行数翻倍。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if _console_enabled():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 不往上冒泡到 root：uvicorn 会给自己的 logger（以及 root）挂 handler，
    # 冒泡会让同一条日志被打印两遍。
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """模块级 logger，例如 `get_logger("server.query")`。

    返回 `star_identification.<name>` 子 logger，向上冒泡到根 logger，
    因此共用同一个文件 handler（和同一个 app.log）。
    """
    setup_logger(ROOT_LOGGER_NAME)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


# 模块级默认 logger，方便 `from agent.logger import logger` 直接用
logger = setup_logger()
