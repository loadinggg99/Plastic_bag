"""六个域工具的公共逻辑。

- collect_urls：从 Tavily 原始返回中收集真实链接，用于回填 source_url（不经过 LLM）。
- extract_structured：搜索结果 → 结构化 LLM → to_display() 文本。
- stringify：把 Tavily 返回压成纯文本，供两路搜索结果拼接。
"""
import time

from langchain_core.documents import Document

from agent.logger import get_logger

logger = get_logger("agent.tools")


def _short(text: str, limit: int = 40) -> str:
    """截断文本，用于日志。"""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def collect_urls(*search_results) -> list[str]:
    """收集 http(s) 链接并按出现顺序去重。

    兼容 {"results": [...]}、list、单条 dict 和 Document 形态。
    """
    found: list[str] = []

    def visit(obj):
        if isinstance(obj, Document):
            url = (obj.metadata or {}).get("url")
            if isinstance(url, str):
                found.append(url)
            return

        if isinstance(obj, dict):
            url = obj.get("url")
            if isinstance(url, str):
                found.append(url)
            results = obj.get("results")
            if results is not None:
                visit(results)
            return

        if isinstance(obj, (list, tuple)):
            for item in obj:
                visit(item)

    for result in search_results:
        visit(result)

    urls: list[str] = []
    seen: set[str] = set()
    for url in found:
        url = url.strip()
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def extract_structured(search_result, structured_llm, hint: str, *, sources=None) -> str:
    """调用结构化 LLM 抽取字段，返回 to_display() 文本。

    Args:
        search_result: Tavily 返回值（str 或 {"results": [...]}）。
        structured_llm: with_structured_output(...) 后的 Runnable。
        hint: 领域说明，写入抽取提示词。
        sources: 收集来源 URL 的原始 payload，默认为 search_result。
            两路搜索拼接成字符串的工具需显式传入两路原始返回值。

    Returns:
        to_display() 文本；结构化输出未生效时退化为 str(result)。
    """
    prompt = f"""根据以下搜索结果，提取企业的{hint}。找不到的字段返回 null。

    搜索结果：
    {search_result}
    """

    started = time.perf_counter()
    logger.info("结构化抽取开始：%s（材料 %d 字符）", _short(hint), len(prompt))
    try:
        result = structured_llm.invoke(prompt)
    except Exception:
        logger.exception("结构化抽取失败：%s", _short(hint))
        raise

    if hasattr(result, "to_display"):
        # source_url 由代码回填，不交给模型生成
        raw_sources = (search_result,) if sources is None else sources
        urls = collect_urls(*raw_sources)
        if hasattr(result, "source_url"):
            result.source_url = "、".join(urls) if urls else None
        display = result.to_display()
        logger.info(
            "结构化抽取完成：%s（输出 %d 字符，来源链接 %d 条，耗时 %.2fs）",
            _short(hint),
            len(display),
            len(urls),
            time.perf_counter() - started,
        )
        return display

    logger.warning(
        "结构化输出未生效（返回 %s），退化为纯文本：%s",
        type(result).__name__,
        _short(hint),
    )
    return str(result)


def stringify(search_result) -> str:
    """把 Tavily 返回值压成纯文本。"""
    if isinstance(search_result, str):
        return search_result

    if isinstance(search_result, dict):
        results = search_result.get("results")
        if results is None:
            return str(search_result)
        return "\n".join(stringify(item) for item in results)

    if isinstance(search_result, (list, tuple)):
        return "\n".join(stringify(item) for item in search_result)

    if isinstance(search_result, Document):
        return search_result.page_content

    return str(search_result)
