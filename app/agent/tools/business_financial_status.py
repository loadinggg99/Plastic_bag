# app/agent/tools/business_financial_status.py
"""经营与财务状况——财务、上市、对外投资、融资与年报。"""
from langchain.tools import tool

from agent.llm import finance_llm
from agent.tools import extract_structured, stringify
from agent.tools.tavily_client import tavily_search_tool


@tool
def get_business_financial_status(company_name: str) -> str:
    """查询公司的财务数据、上市信息、对外投资、分支机构、融资历史、年报和招投标。

    覆盖：财务数据（营收、净利润、资产负债等，以上市公司为主）、上市信息
    （股票代码、上市日期、板块、股价行情）、对外投资（直接投资的企业及持股
    比例）、分支机构（分公司/子公司）、融资历史（轮次、时间、金额、投资方）、
    企业年报（资产状况、社保人数）、招投标（招标与中标公告）。

    注意：非上市公司通常只有融资历史和年报公示，财务与上市字段大概是空的。

    Args:
        company_name: 要查询的公司名称
    """
    # 第一次搜索：财务与上市
    finance_result = tavily_search_tool.invoke(
        {
            "query": (
                f"{company_name} 财务数据 营收 净利润 资产负债 "
                f"上市信息 股票代码 上市日期 板块 股价"
            )
        }
    )

    # 第二次搜索：投资、分支、融资与年报
    investment_result = tavily_search_tool.invoke(
        {
            "query": (
                f"{company_name} 对外投资 持股比例 分支机构 分公司 子公司 "
                f"融资历史 融资轮次 投资方 企业年报 招投标 中标公告"
            )
        }
    )

    search_result = (
        f"【财务与上市信息】\n{stringify(finance_result)}\n\n"
        f"【投资、分支、融资与年报】\n{stringify(investment_result)}"
    )

    return extract_structured(
        search_result,
        finance_llm,
        "经营与财务状况信息（财务数据、上市信息、对外投资、分支机构、融资历史、企业年报、招投标）",
        sources=(finance_result, investment_result),
    )
