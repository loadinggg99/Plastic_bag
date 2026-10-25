# app/server/routes/query.py
"""查询接口：POST /api/query"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.server.dependencies import invoke_agent
from app.server.report_store import report_store
from app.server.sections import parse_report

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    """搜索框提交的内容。query 会原样变成 HumanMessage。"""

    query: str = Field(..., min_length=1, description="搜索框输入，将原样作为 HumanMessage")
    thread_id: str = Field(default="web", description="会话 id，可选")


@router.post("/api/query")
def query_enterprise(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="请输入企业名称")

    try:
        content = invoke_agent(query, req.thread_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"查询失败：{exc}")

    # 把整段结果拆成六个板块并缓存，前端随后跳转到 /report/{report_id}
    parsed = parse_report(str(content))
    report = report_store.put(
        company=query,
        raw=str(content),
        intro=parsed.intro,
        sections=parsed.sections,
        fallback=parsed.fallback,
    )

    return {
        "ok": True,
        "content": content,
        "company": query,
        "report_id": report.id,
        "report_url": f"/report/{report.id}",
    }
