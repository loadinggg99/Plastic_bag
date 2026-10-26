# app/agent/config/basic_config.py
"""基础配置。

两个关键点：
1. 字段必须带类型注解，否则 Pydantic 2 会在导入时直接抛 PydanticUserError。
2. 路径全部用「基于 __file__ 算出来的绝对路径」，而不是写成 "./resources/..."。
   写相对路径会跟着当前工作目录漂移（在项目根跑是 <根>/resources，
   在 app/agent 下跑就变成 app/agent/resources），换个目录启动就找不到
   .env 和数据库了。

目录结构（全部在 app/agent/resources/ 下）：
- app/agent/resources/db/        sqlite 数据库文件
- app/agent/resources/logs/      日志
- app/agent/resources/prompts/   prompt 模板
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 本文件位于 app/agent/config/basic_config.py
AGENT_DIR = Path(__file__).resolve().parent.parent   # -> app/agent/
APP_DIR = AGENT_DIR.parent                           # -> app/（uv 项目根）
ENV_FILE = APP_DIR / ".env"

RESOURCES_DIR = AGENT_DIR / "resources"   # 资源根目录
DB_DIR = RESOURCES_DIR / "db"             # 数据库文件专用目录
LOG_DIR = RESOURCES_DIR / "logs"          # 日志目录


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,          # 绝对路径，不随工作目录漂移
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # 模型配置
    main_model: str = "deepseek-flash"
    # 结构化抽取专用的模型。必须是"非思考"模型，原因见 app/agent/llm.py 里的注释：
    # deepseek-flash 是思考模型，不接受任何 tool_choice，而
    # with_structured_output(method="function_calling") 一定会强制 tool_choice。
    structured_model: str = "deepseek-chat"
    api_key: str = Field(alias="DEEPSEEK_API_KEY")
    base_url: str = "https://api.deepseek.com"

    # 上下文
    num_ctx: int = 8192      # 上下文窗口的最大 token 总数（提示词+历史对话+生成内容）
    num_predict: int = 4096   # 单次回答最大 token 生成量

    # 中间件
    summary_model: str = "deepseek-flash"
    summary_model_api_key: str = Field(alias="DEEPSEEK_API_KEY")
    summary_model_base_url: str = "https://api.deepseek.com"
    summary_trigger_tokens: int = 8192          # 总结触发 token 数
    summary_keep_messages: int = 8              # 保留的会话数

    # tavily工具
    # Tavily 官方 limit：max_results 取值 1-20。传 21 或 50 不会报错，
    # 但服务端会静默降级成 10 条，反而比 20 更少。
    tavily_api_key: str = Field(alias="TAVILY_API_KEY")
    tavily_max_results: int = Field(default=10, ge=1, le=20)
    tavily_topic: str = "general"

    # 储存：统一放在 app/agent/resources/ 下
    # 等价于原来的 "./resources/checkpoint.db"，但不再依赖当前工作目录；
    # 目录不存在时由 init_sqlite() 自动创建（sqlite 自己不会建目录）。
    db_path: Path = DB_DIR / "checkpoint.db"    # 数据库储存路径
    log_path: Path = LOG_DIR                    # 日志储存路径


settings = Config()
