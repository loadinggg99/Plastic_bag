"""FastAPI 应用：中间件、路由、静态资源。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.config import settings
from server.routes import api_router
from server.security import SecurityHeadersMiddleware

# 仅暴露首页与该三个静态目录，避免把 frontend/ 整个挂到同源下
_FRONTEND_ASSET_DIRS = ("assets", "css", "js")
_INDEX_HEADERS = {"Cache-Control": "no-cache"}


def _mount_frontend(application: FastAPI) -> None:
    frontend_dir = settings.frontend_dir

    @application.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html", headers=_INDEX_HEADERS)

    @application.api_route("/index.html", methods=["GET", "HEAD"], include_in_schema=False)
    def index_html() -> FileResponse:
        return FileResponse(frontend_dir / "index.html", headers=_INDEX_HEADERS)

    for name in _FRONTEND_ASSET_DIRS:
        application.mount(
            f"/{name}",
            StaticFiles(directory=str(frontend_dir / name)),
            name=name,
        )


def create_app() -> FastAPI:
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

    # 后添加的中间件在外层，CORS 预检响应也会带上安全头
    application.add_middleware(SecurityHeadersMiddleware)

    application.include_router(api_router)
    _mount_frontend(application)   # 必须最后挂载，避免覆盖 /api 与 /docs
    return application


app = create_app()
