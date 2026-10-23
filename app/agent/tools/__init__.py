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
"""
from langchain_core.documents import Document


def extract_structured(search_result, structured_llm, hint: str) -> str:
    """把 Tavily 的搜索结果交给结构化 LLM，返回格式化文本。

    Args:
        search_result: tavily_search_tool.invoke(...) 的返回值，
            可能是 str，也可能是 {"results": [...]} 这样的 dict。
        structured_llm: with_structured_output(<Pydantic 模型>) 后的 Runnable，
            正常返回该 Pydantic 实例。
        hint: 领域提示，用于告诉模型这次要抽哪一类字段。

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
