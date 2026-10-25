# app/server/security.py
"""安全响应头（XSS / 点击劫持 / MIME 嗅探防护）。

前端只加载同源的 `index.html`、`css/style.css`、`js/app.js`；服务端渲染的
Jinja2 模板也没有内联脚本、没有内联事件处理器，所以 CSP 可以收得很紧。
`require-trusted-types-for` 会在支持的浏览器里直接禁掉 innerHTML 一类 DOM XSS
注入点；首页 JS 只使用 `textContent` / `createElement`，不会触发。

注意：Swagger UI / ReDoc 依赖 CDN 和内联脚本，套这份 CSP 会白屏，
所以 `/docs`、`/redoc`、`/openapi.json` 单独跳过 CSP（其余安全头照常）。
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'none'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "script-src 'self'",
        "script-src-attr 'none'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "manifest-src 'self'",
        "worker-src 'none'",
        # DOM XSS 的最后一道防线：禁掉 innerHTML 等注入 sink
        "require-trusted-types-for 'script'",
        "trusted-types 'none'",
    )
)

# 这些路径由 FastAPI 自动生成，页面里带 CDN 资源/内联脚本
_CSP_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json")

_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """给所有响应补上安全头；CSP 只对本站前端页面生效。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", _PERMISSIONS_POLICY)
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if not request.url.path.startswith(_CSP_EXEMPT_PREFIXES):
            response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)

        # 只在 HTTPS 下发 HSTS（本地 http://127.0.0.1 下浏览器本来也会忽略）
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response
