# app/agent/tools/risk_judicial_info.py
"""风险与司法信息——评估公司合规与信用状况的关键。"""
from langchain.tools import tool

from agent.llm import risk_llm
from agent.tools import extract_structured, stringify
from agent.tools.tavily_client import tavily_search_tool


@tool
def get_risk_judicial_info(company_name: str) -> str:
    """查询公司的司法风险、执行信息、经营风险、税务风险和破产重整。

    覆盖：司法风险（法律诉讼、法院公告、开庭公告、裁判文书）、执行信息
    （被执行人、失信被执行人、限制消费令、终本案件）、经营风险（经营异常、
    行政处罚、股权出质、股权冻结、动产抵押）、税务风险（欠税公告、税务异常）、
    破产重整（破产案件信息）。

    注意：只检索公开披露的信息，结果可能滞后，或与官方渠道（国家企业信用信息
    公示系统、中国执行信息公开网、裁判文书网等）不一致，不能作为尽调结论。

    Args:
        company_name: 要查询的公司名称
    """
    # 第一次搜索：司法与执行
    judicial_result = tavily_search_tool.invoke(
        {
            "query": (
                f"{company_name} 法律诉讼 裁判文书 开庭公告 法院公告 "
                f"被执行人 失信被执行人 限制消费令 终本案件"
            )
        }
    )

    # 第二次搜索：经营、税务与破产
    operation_risk_result = tavily_search_tool.invoke(
        {
            "query": (
                f"{company_name} 经营异常 行政处罚 股权出质 股权冻结 动产抵押 "
                f"欠税公告 税务异常 破产重整 破产案件"
            )
        }
    )

    search_result = (
        f"【司法与执行信息】\n{stringify(judicial_result)}\n\n"
        f"【经营、税务与破产风险】\n{stringify(operation_risk_result)}"
    )

    return extract_structured(
        search_result,
        risk_llm,
        "风险与司法信息（司法风险、执行信息、经营风险、税务风险、破产重整）",
        sources=(judicial_result, operation_risk_result),
    )
