"""服务配置。"""
from dataclasses import dataclass, field
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2]    # app/
REPO_DIR = APP_DIR.parent                        # 仓库根（frontend/ 所在）


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    title: str = "星鉴"
    description: str = "企业信息查询 Agent 后端接口"
    version: str = "0.1.0"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    frontend_dir: Path = REPO_DIR / "frontend"
    templates_dir: Path = APP_DIR / "server" / "templates"

    # 报告在内存中保留的时长与条数上限
    report_ttl_seconds: int = 3600
    report_max_entries: int = 200

    # 同时执行的查询数上限：超出的请求排队，保护上游 API 与进程资源
    max_concurrent_queries: int = 3


settings = Settings()
