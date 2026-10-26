# app/agent/config/database_config.py
"""数据库配置。

注意：Pydantic 2 的模型字段在类上是取不到的（`DbConfig.DATABASE_URI`
会抛 AttributeError），必须通过实例访问，所以这里导出一个实例 `dbConfig`。
路径统一来源于 `settings.db_path`，避免两处配置各写一份。
"""
from pathlib import Path

from pydantic import BaseModel, Field

from agent.config.basic_config import settings


class DbConfig(BaseModel):
    DATABASE_URI: Path = Field(default=settings.db_path)


dbConfig = DbConfig()
