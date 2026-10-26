"""知识产权与资质工具。"""
from langchain.tools import tool

from agent.llm import ip_llm
from agent.tools import extract_structured
from agent.tools.tavily_client import search


@tool
def get_ip_qualification(company_name: str) -> str:
    """查询公司的知识产权、资质证书和网站备案。

    覆盖：知识产权（商标、专利、著作权、软件著作权）、资质证书（各类行政许可、
    行业资质）、网站备案（公司官网的 ICP 备案信息）。

    注意：商标专利的准确数量与法律状态以国家知识产权局公开数据为准。

    Args:
        company_name: 要查询的公司名称
    """
    search_result = search(
        f"{company_name} 商标 专利 著作权 软件著作权 "
        f"资质证书 行政许可 行业资质 ICP备案 网站备案"
    )

    return extract_structured(
        search_result,
        ip_llm,
        "知识产权与资质信息（商标、专利、著作权、软件著作权、资质证书、行政许可、网站备案）",
    )
