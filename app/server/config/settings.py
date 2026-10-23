# app/server/config/settings.py
"""星鉴后端服务配置。"""
from dataclasses import dataclass, field
from pathlib import Path

# 本文件位于 app/server/config/settings.py，向上三级到项目根
PROJECT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    title: str = "星鉴"
    description: str = "企业信息查询 Agent 后端接口"
    version: str = "0.1.0"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    frontend_dir: Path = PROJECT_DIR / "frontend"


settings = Settings()
