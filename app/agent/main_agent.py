"""Agent 构建入口。

build_agent() 组装模型、六个域工具、摘要中间件和 checkpointer；
模块级 test_agent 供 langgraph.json 引用。
"""
from agent.config import settings
from agent.database import init_sqlite
from agent.llm import main_llm, summary_model
from agent.logger import get_logger
from agent.prompts.prompt import load_prompt_template
from agent.tools.basic_business_info import get_basic_business_info
from agent.tools.business_financial_status import get_business_financial_status
from agent.tools.ip_qualification import get_ip_qualification
from agent.tools.operation_public_opinion import get_operation_public_opinion
from agent.tools.personnel_equity_structure import get_personnel_equity_structure
from agent.tools.risk_judicial_info import get_risk_judicial_info

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

logger = get_logger("agent.main_agent")

TOOLS = [
    get_basic_business_info,
    get_personnel_equity_structure,
    get_business_financial_status,
    get_risk_judicial_info,
    get_ip_qualification,
    get_operation_public_opinion,
]


def build_agent(storage_mode: str = "Sqlite"):
    """创建 Agent。

    Args:
        storage_mode: "RAM" 会话仅存内存；"Sqlite" 持久化到 settings.db_path。

    Raises:
        ValueError: storage_mode 不是 "RAM" / "Sqlite"。
    """
    if storage_mode == "RAM":
        checkpointer = InMemorySaver()
    elif storage_mode == "Sqlite":
        checkpointer = init_sqlite()
    else:
        raise ValueError(f"未知的存储类型：{storage_mode!r}（可选 'RAM' / 'Sqlite'）")

    middleware = SummarizationMiddleware(
        model=summary_model,
        trigger=("tokens", settings.summary_trigger_tokens),
        keep=("messages", settings.summary_keep_messages),
    )

    agent = create_agent(
        model=main_llm,
        system_prompt=load_prompt_template("enterprise_inquiry"),
        tools=TOOLS,
        middleware=[middleware],
        checkpointer=checkpointer,
    )

    logger.info(
        "构建 agent：storage_mode=%s，工具 %d 个，主模型=%s，总结模型=%s",
        storage_mode,
        len(TOOLS),
        settings.main_model,
        settings.summary_model,
    )
    return agent


# langgraph.json 的入口：langgraph dev / 打包时按引用加载
test_agent = build_agent(storage_mode="RAM")
