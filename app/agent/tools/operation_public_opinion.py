# app/agent/tools/operation_public_opinion.py
"""经营状况与舆情——员工规模、招聘、新闻舆情与企业评分。"""
from langchain.tools import tool

from agent.llm import opinion_llm
from agent.tools import extract_structured, stringify
from agent.tools.tavily_client import tavily_search_tool


@tool
def get_operation_public_opinion(company_name: str) -> str:
    """查询公司的员工规模、招聘信息、新闻舆情和企业评分。

    覆盖：员工规模（参保人数、人员规模）、招聘信息（招聘职位、薪资范围）、
    新闻舆情（相关新闻、公告、自媒体信息）、企业评分（天眼评分或行业评分）。

    Args:
        company_name: 要查询的公司名称
    """
    # 第一次搜索：员工规模与招聘
    staff_result = tavily_search_tool.invoke(
        {"query": f"{company_name} 参保人数 人员规模 员工人数 招聘 职位 薪资范围"}
    )

    # 第二次搜索：新闻舆情与企业评分
    news_result = tavily_search_tool.invoke(
        {"query": f"{company_name} 新闻 舆情 最新动态 公告 天眼评分 企业评分 行业排名"}
    )

    search_result = (
        f"【员工规模与招聘】\n{stringify(staff_result)}\n\n"
        f"【新闻舆情与企业评分】\n{stringify(news_result)}"
    )

    return extract_structured(
        search_result,
        opinion_llm,
        "经营状况与舆情信息（员工规模、招聘信息、新闻舆情、企业评分）",
        sources=(staff_result, news_result),
    )
