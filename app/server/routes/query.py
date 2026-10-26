"""查询接口：POST /api/query"""
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.logger import get_logger
from server.dependencies import invoke_agent
from server.report_store import report_store
from server.sections import parse_report

logger = get_logger("server.query")

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    """搜索框提交的内容。query 会原样变成 HumanMessage。"""

    query: str = Field(..., min_length=1, description="搜索框输入，将原样作为 HumanMessage")
    thread_id: str = Field(default="web", description="会话 id，可选")


@router.post("/api/query")
def query_enterprise(req: QueryRequest):
    query = req.query.strip()
    if not query:
        logger.warning("收到空查询，已拒绝")
        raise HTTPException(status_code=400, detail="请输入企业名称")

    started = time.perf_counter()
    logger.info("收到查询请求：query=%r thread_id=%s", query, req.thread_id)

    try:
        content = invoke_agent(query, req.thread_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("查询接口返回 500：query=%r", query)
        raise HTTPException(status_code=500, detail=f"查询失败：{exc}") from exc

    # 把整段结果拆成六个板块并缓存，前端随后跳转到 /report/{report_id}
    parsed = parse_report(str(content))
    report = report_store.put(
        company=query,
        raw=str(content),
        intro=parsed.intro,
        sections=parsed.sections,
        fallback=parsed.fallback,
    )

    logger.info(
        "查询接口完成：report_id=%s 板块 %d/6 %s 前言=%d字 fallback=%s 总耗时 %.2fs",
        report.id,
        len(parsed.sections),
        list(parsed.sections),
        len(parsed.intro),
        bool(parsed.fallback),
        time.perf_counter() - started,
    )
    if len(parsed.sections) < 6:
        logger.warning(
            "解析后只有 %d/6 个板块，报告页会显示「本次未查询」：%s",
            len(parsed.sections),
            list(parsed.sections),
        )

    return {
        "ok": True,
        "content": content,
        "company": query,
        "report_id": report.id,
        "report_url": f"/report/{report.id}",
    }
