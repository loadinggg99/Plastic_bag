"""人员与股权结构工具。"""
from langchain.tools import tool

from agent.llm import equity_llm
from agent.tools import extract_structured, stringify
from agent.tools.tavily_client import search


@tool
def get_personnel_equity_structure(company_name: str) -> str:
    """查询公司的主要人员、股东、最终受益人、实际控制人和股权穿透关系。

    覆盖：主要人员（法定代表人、董事、监事、经理等高管）、股东信息（股东名称/
    姓名、持股比例、认缴出资额、实缴出资额、出资方式、出资日期）、最终受益人
    （股权穿透后的自然人）、实际控制人、股权穿透图/企业关系图谱。

    注意：最终受益人、实际控制人和穿透层级由公开的股权链条推算，可能与官方
    登记口径不一致，仅作线索。

    Args:
        company_name: 要查询的公司名称
    """
    # 第一次搜索：人和股权明细
    personnel_result = search(
        f"{company_name} 主要人员 法定代表人 董事 监事 经理 高管 "
        f"股东信息 持股比例 认缴出资额 实缴出资额 出资方式 出资日期"
    )

    # 第二次搜索：股权穿透（谁最终受益、谁实际控制）
    penetration_result = search(
        f"{company_name} 实际控制人 最终受益人 股权穿透 "
        f"股权结构图 企业关系图谱 控股股东 受益所有人"
    )

    # 两路结果拼成一份材料再抽取，免得模型只看到一半
    search_result = (
        f"【人员与股东信息】\n{stringify(personnel_result)}\n\n"
        f"【股权穿透与实控人】\n{stringify(penetration_result)}"
    )

    return extract_structured(
        search_result,
        equity_llm,
        "人员与股权结构信息（主要人员、股东信息、最终受益人、实际控制人、股权穿透关系）",
        sources=(personnel_result, penetration_result),
    )
