"""基础配置：模型、Tavily、路径。

路径一律基于 __file__ 计算为绝对路径，不依赖当前工作目录。
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_DIR = Path(__file__).resolve().parent.parent   # app/agent
APP_DIR = AGENT_DIR.parent                           # app/（uv 项目根）
ENV_FILE = APP_DIR / ".env"

RESOURCES_DIR = AGENT_DIR / "resources"
DB_DIR = RESOURCES_DIR / "db"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    main_model: str = "deepseek-flash"
    structured_model: str = "deepseek-chat"   # 必须是非思考模型，见 llm.py
    api_key: str = Field(alias="DEEPSEEK_API_KEY")
    base_url: str = "https://api.deepseek.com"

    summary_model: str = "deepseek-flash"
    summary_model_api_key: str = Field(alias="DEEPSEEK_API_KEY")
    summary_model_base_url: str = "https://api.deepseek.com"
    summary_trigger_tokens: int = 8192
    summary_keep_messages: int = 8

    tavily_api_key: str = Field(alias="TAVILY_API_KEY")
    # Tavily 只接受 1-20；超出会被服务端静默降级为 10 条
    tavily_max_results: int = Field(default=10, ge=1, le=20)
    tavily_topic: str = "general"

    db_path: Path = DB_DIR / "checkpoint.db"


settings = Config()
