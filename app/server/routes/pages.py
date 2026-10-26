"""服务端渲染页面：调研结果页 + 六个板块详情页。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from agent.logger import get_logger
from server.config import settings
from server.report_store import report_store
from server.sections import (
    DOMAIN_BY_KEY,
    DOMAINS,
    FALLBACK_ICON,
    render_section_html,
)

logger = get_logger("server.pages")

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


def _context(**kwargs):
    return {"site_name": settings.title, **kwargs}


def _error(
    request: Request,
    *,
    title: str,
    message: str,
    back_url: str = "/",
    back_label: str = "返回首页",
    status_code: int = 404,
):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context=_context(
            error_title=title,
            error_message=message,
            back_url=back_url,
            back_label=back_label,
        ),
        status_code=status_code,
    )


def _expired(request: Request, report_id: str):
    logger.warning("报告不存在或已过期：report_id=%s path=%s", report_id, request.url.path)
    minutes = max(1, settings.report_ttl_seconds // 60)
    return _error(
        request,
        title="报告不存在或已过期",
        message=f"报告在服务端只保留约 {minutes} 分钟，请返回首页重新查询。",
    )


@router.get("/report/{report_id}", response_class=HTMLResponse)
def report_page(request: Request, report_id: str):
    """2×3 的六个板块导航页。"""
    report = report_store.get(report_id)
    if report is None:
        return _expired(request, report_id)

    domains = [
        {
            "key": domain.key,
            "title": domain.title,
            "description": domain.description,
            "icon": domain.icon,
            "available": domain.key in report.sections,
            "url": f"/report/{report.id}/{domain.key}",
        }
        for domain in DOMAINS
    ]

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context=_context(report=report, domains=domains),
    )


@router.get("/report/{report_id}/{section_key}", response_class=HTMLResponse)
def section_page(request: Request, report_id: str, section_key: str):
    """单个板块的详情页；section_key=all 时查看完整内容。"""
    report = report_store.get(report_id)
    if report is None:
        return _expired(request, report_id)

    if section_key == "all":
        domain = None
        section_title = "完整内容"
        body = report.fallback or report.raw
        icon_markup = FALLBACK_ICON
        available = bool(body.strip())
    else:
        domain = DOMAIN_BY_KEY.get(section_key)
        if domain is None:
            return _error(
                request,
                title="板块不存在",
                message="请返回调研结果重新选择板块。",
                back_url=f"/report/{report.id}",
                back_label="返回调研结果",
            )
        section_title = domain.title
        body = report.sections.get(section_key)
        icon_markup = domain.icon
        available = body is not None

    return templates.TemplateResponse(
        request=request,
        name="section.html",
        context=_context(
            report=report,
            domain=domain,
            section_title=section_title,
            icon_markup=icon_markup,
            available=available,
            content_html=render_section_html(body or ""),
        ),
    )
