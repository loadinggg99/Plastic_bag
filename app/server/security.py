"""安全响应头：CSP、HSTS 及常规防护头。

前端只加载同源资源且页面无内联脚本，因此 CSP 可以收得很紧；
/docs、/redoc、/openapi.json 依赖 CDN 与内联脚本，跳过 CSP。
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
        "require-trusted-types-for 'script'",
        "trusted-types 'none'",
    )
)

_CSP_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json")
_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """为所有响应补充安全头；CSP 仅作用于本站页面。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", _PERMISSIONS_POLICY)
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if not request.url.path.startswith(_CSP_EXEMPT_PREFIXES):
            response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)

        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response
