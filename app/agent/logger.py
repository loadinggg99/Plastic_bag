"""统一日志：一条日志 = MongoDB 里的一个文档（可选同时打控制台）。

参数全在 `agent.config.database_config.LogConfig`。用法：

    from agent.logger import get_logger
    logger = get_logger("server.query")
    logger.info("...")

文档结构：{time, level, logger, message}（异常时 message 里带 traceback）。
"""
from __future__ import annotations

import logging
import sys
import time
from datetime import UTC, datetime

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from agent.config.database_config import logConfig

ROOT_LOGGER_NAME = "star_identification"


class MongoHandler(logging.Handler):
    """把日志 insert 进 MongoDB。"""

    def __init__(self) -> None:
        super().__init__()
        self.collection = MongoClient(
            logConfig.MONGO_URI,
            serverSelectionTimeoutMS=1000,
        )[logConfig.MONGO_DB][logConfig.MONGO_COLLECTION]
        self._retry_at = 0.0

    def emit(self, record: logging.LogRecord) -> None:
        # Mongo 挂了就退避一会儿，别让每条日志都卡一次连接超时
        if time.monotonic() < self._retry_at:
            return
        try:
            self.collection.insert_one(
                {
                    "time": datetime.now(UTC),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": self.format(record),
                }
            )
        except PyMongoError as exc:
            # 只提示一次，退避 RETRY_SECONDS 秒；不打整段栈，免得刷屏
            self._retry_at = time.monotonic() + logConfig.RETRY_SECONDS
            print(f"[logger] MongoDB 写入失败（{logConfig.RETRY_SECONDS}s 后重试）：{exc}", file=sys.stderr)


def setup_logger(name: str = ROOT_LOGGER_NAME) -> logging.Logger:
    """同名 logger 只配一次 handler：重复调用不会重复写库。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logConfig.LEVEL)
    logger.addHandler(MongoHandler())

    if logConfig.CONSOLE:
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(console)

    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """模块级子 logger，例如 get_logger("server.query")，共用同一套 handler。"""
    setup_logger(ROOT_LOGGER_NAME)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


logger = setup_logger()
