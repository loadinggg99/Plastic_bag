# app/server/routes/__init__.py
"""路由汇总。"""
from fastapi import APIRouter

from server.routes.pages import router as pages_router
from server.routes.query import router as query_router

api_router = APIRouter()
api_router.include_router(query_router)
api_router.include_router(pages_router)

__all__ = ["api_router"]
