"""基础工商信息工具。"""
from langchain.tools import tool

from agent.llm import basic_info_llm
from agent.tools import extract_structured
from agent.tools.tavily_client import search


@tool
def get_basic_business_info(company_name: str) -> str:
    """查询公司的基础工商信息。

    覆盖：企业名称与曾用名、统一社会信用代码/工商注册号/组织机构代码/纳税人
    识别号、法定代表人、注册资本（认缴与实缴）、成立日期、营业期限、经营状态、
    企业类型、注册地址、经营范围、登记机关与核准日期、所属行业。

    Args:
        company_name: 要查询的公司名称
    """
    search_result = search(
        f"{company_name} 工商信息 统一社会信用代码 法定代表人 注册资本 "
        f"成立日期 经营状态 企业类型 注册地址 经营范围 登记机关 所属行业"
    )

    return extract_structured(
        search_result,
        basic_info_llm,
        "基础工商信息（名称、曾用名、各类代码、法定代表人、注册资本、成立日期、"
        "营业期限、经营状态、企业类型、注册地址、经营范围、登记机关、核准日期、所属行业）",
    )
