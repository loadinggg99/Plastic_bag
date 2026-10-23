# app/server/__init__.py
"""星鉴后端：FastAPI 应用。

结构：
- config/         服务配置（host、port、前端目录、CORS 等）
- routes/         路由（/api/query 等）
- dependencies.py 共享依赖（agent 单例、调用封装）
- main.py         命令行入口

启动：
    uvicorn app.server:app --reload
    python -m app.server.main
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.server.config import settings
from app.server.routes import api_router


def create_app() -> FastAPI:
    """组装 FastAPI 应用：中间件 → 路由 → 静态文件。"""
    application = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    # 静态文件挂载必须放在最后，避免覆盖 /api 与 /docs 路由
    application.mount(
        "/",
        StaticFiles(directory=str(settings.frontend_dir), html=True),
        name="frontend",
    )
    return application


app = create_app()
