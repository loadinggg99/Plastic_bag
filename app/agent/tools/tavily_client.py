"""Tavily 搜索封装（统一日志与耗时）。"""
import time

from agent.config import settings
from agent.logger import get_logger
from langchain_tavily import TavilySearch

logger = get_logger("agent.tools.tavily")

# 显式传 key：pydantic-settings 只把 .env 读进 settings，不写入 os.environ
tavily_search_tool = TavilySearch(
    tavily_api_key=settings.tavily_api_key,
    max_results=settings.tavily_max_results,
    topic=settings.tavily_topic,
)


def _result_count(result) -> int:
    """统计返回条数（仅用于日志；兼容 dict / list / str）。"""
    if isinstance(result, dict):
        results = result.get("results")
        if isinstance(results, list):
            return len(results)
        return 1 if results else 0
    if isinstance(result, (list, tuple)):
        return len(result)
    return 1 if str(result).strip() else 0


def search(query: str):
    """执行一次 Tavily 搜索并记录耗时；所有工具都应走这里。"""
    started = time.perf_counter()
    logger.info("Tavily 搜索：%s", query)
    try:
        result = tavily_search_tool.invoke({"query": query})
    except Exception:
        logger.exception("Tavily 搜索失败：%s", query)
        raise

    logger.info(
        "Tavily 返回 %d 条，耗时 %.2fs",
        _result_count(result),
        time.perf_counter() - started,
    )
    return result
