# app/server/__init__.py
"""星鉴后端：FastAPI 应用。

结构：
- config/         服务配置（host、port、前端目录、模板目录、报告缓存等）
- routes/         路由（/api/query、/report/{id}、/report/{id}/{section}）
- templates/      Jinja2 模板（六板块网格页 / 板块详情页 / 错误页）
- dependencies.py 共享依赖（agent 单例、调用封装）
- security.py     安全响应头（CSP、X-Content-Type-Options 等）
- sections.py     六板块元数据、SVG 图标、解析与安全 HTML 渲染
- report_store.py 内存报告缓存（TTL + 容量上限）
- main.py         命令行入口

启动：
    uvicorn app.server:app --reload
    python -m app.server.main
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.server.config import settings
from app.server.routes import api_router
from app.server.security import SecurityHeadersMiddleware

# 前端真正需要对外暴露的静态目录
_FRONTEND_ASSET_DIRS = ("assets", "css", "js")


def _mount_frontend(application: FastAPI) -> None:
    """只挂载前端需要的静态资源，而不是整个 frontend/ 目录。

    直接 mount 整个 frontend/ 会把 node_modules/、package.json、dist/ 等
    一起放到同源下：既泄露源码，也扩大了「同源任意 HTML/JS」的 XSS 攻击面。
    这里只暴露 index.html 和 assets/css/js 三个目录。
    """
    frontend_dir = settings.frontend_dir

    # no-cache：HTML 每次重新校验，保证新的安全头/资源版本能及时生效
    _INDEX_HEADERS = {"Cache-Control": "no-cache"}

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

    # 后添加的中间件在更外层，保证 CORS 预检等响应也带上安全头
    application.add_middleware(SecurityHeadersMiddleware)

    application.include_router(api_router)

    # 静态文件挂载必须放在最后，避免覆盖 /api 与 /docs 路由
    _mount_frontend(application)
    return application


app = create_app()
