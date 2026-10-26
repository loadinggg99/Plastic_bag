"""数据库与日志配置。

Pydantic 2 的字段只能通过实例访问（`DbConfig.DATABASE_URI` 会抛 AttributeError），
因此对外导出 `dbConfig` / `logConfig` 实例。
"""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agent.config.basic_config import settings


class DbConfig(BaseModel):
    DATABASE_URI: Path = Field(default=settings.db_path)


class LogConfig(BaseModel):
    """日志写 MongoDB：一条日志 = 一个文档。"""

    MONGO_URI: str = Field(default="mongodb://127.0.0.1:27017")
    MONGO_DB: str = Field(default="star_identification")
    MONGO_COLLECTION: str = Field(default="logs")

    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    CONSOLE: bool = Field(default=True)   # 是否同时输出到控制台

    # Mongo 连不上时退避多久再试（秒），避免每条日志都卡一次连接超时
    RETRY_SECONDS: int = Field(default=60, ge=0)


dbConfig = DbConfig()
logConfig = LogConfig()
