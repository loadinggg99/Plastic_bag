# app/agent/tools/__init__.py
"""工具包统一出口。

六个域名的工具函数一一对应《企业信息内容.md》的六个章节：

| 工具函数                          | 模块                              | 对应章节         |
|-----------------------------------|-----------------------------------|------------------|
| `get_basic_business_info`         | `basic_business_info.py`          | 基础工商信息     |
| `get_personnel_equity_structure`  | `personnel_equity_structure.py`   | 人员与股权结构   |
| `get_business_financial_status`   | `business_financial_status.py`    | 经营与财务状况   |
| `get_risk_judicial_info`          | `risk_judicial_info.py`           | 风险与司法信息   |
| `get_ip_qualification`            | `ip_qualification.py`             | 知识产权与资质   |
| `get_operation_public_opinion`    | `operation_public_opinion.py`     | 经营状况与舆情   |

`extract_structured` 是六个工具共用的抽取函数：Tavily 搜索 → 结构化 LLM 抽取
→ `to_display()` 格式化，避免每个工具都抄一遍"拼 prompt + 判断退化"的逻辑。
放在这里而不是 `app/utils.py`，是因为它只服务于工具层。

数据来源 URL 也在这里统一处理：`collect_urls()` 从 Tavily 原始返回值里收集
真实链接，再由 `extract_structured()` 写回模型的 `source_url` 字段。链接不经过
LLM，避免模型编造。
"""
from langchain_core.documents import Document


def collect_urls(*search_results) -> list[str]:
    """从 Tavily 搜索结果里收集 http(s) 链接，按出现顺序去重。

    兼容三种常见形态：
    - `{"results": [{"content": ..., "url": ...}, ...]}`
    - `[...]` / 单条 `{"url": ...}`
    - `Document(metadata={"url": ...})`

    Returns:
        去重后的链接列表；只保留 http/https，避免把 `javascript:` 之类的
        链接带到前端。
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
    """把 Tavily 的搜索结果交给结构化 LLM，返回格式化文本。

    Args:
        search_result: tavily_search_tool.invoke(...) 的返回值，
            可能是 str，也可能是 {"results": [...]} 这样的 dict。
        structured_llm: with_structured_output(<Pydantic 模型>) 后的 Runnable，
            正常返回该 Pydantic 实例。
        hint: 领域提示，用于告诉模型这次要抽哪一类字段。
        sources: 用于收集「数据来源URL」的 Tavily 原始返回值，可传多个。
            默认用 `search_result` 本身。搜了两路并拼成字符串的工具要显式传
            两路的原始 payload——拼字符串时 URL 已经丢了。

    Returns:
        结构化模型 `to_display()` 生成的文本；万一结构化没生效
        （返回的是 AIMessage 之类），退化成 str(result)。
    """
    prompt = f"""根据以下搜索结果，提取企业的{hint}。找不到的字段返回 null。

    搜索结果：
    {search_result}
    """

    result = structured_llm.invoke(prompt)

    # 万一结构化没生效，返回的是 AIMessage
    if hasattr(result, "to_display"):
        # 数据来源 URL 由代码从原始搜索结果回填，不交给模型生成。
        raw_sources = (search_result,) if sources is None else sources
        urls = collect_urls(*raw_sources)
        if hasattr(result, "source_url"):
            result.source_url = "、".join(urls) if urls else None
        return result.to_display()
    return str(result)


def stringify(search_result) -> str:
    """把 Tavily 的返回值统一压成纯文本，供需要二次搜索的提示词拼接。

    TavilySearch 通常返回 {"results": [{"content": ..., "url": ...}, ...]}，
    但也可能因为 max_results 或异常返回 str / list。
    """
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
