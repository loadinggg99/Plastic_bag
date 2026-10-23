# 内部模块
from app.agent.config import settings
from app.agent.database import init_sqlite
from app.agent.llm import main_llm, summary_model
from app.agent.prompts.prompt import load_prompt_template

# 六个域的工具
from app.agent.tools.basic_business_info import get_basic_business_info
from app.agent.tools.business_financial_status import get_business_financial_status
from app.agent.tools.ip_qualification import get_ip_qualification
from app.agent.tools.operation_public_opinion import get_operation_public_opinion
from app.agent.tools.personnel_equity_structure import get_personnel_equity_structure
from app.agent.tools.risk_judicial_info import get_risk_judicial_info

# 外部模块
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

# Agent 可用的全部工具
TOOLS = [
    get_basic_business_info,          # 基础工商信息
    get_personnel_equity_structure,   # 人员与股权结构
    get_business_financial_status,    # 经营与财务状况
    get_risk_judicial_info,           # 风险与司法信息
    get_ip_qualification,             # 知识产权与资质
    get_operation_public_opinion,     # 经营状况与舆情
]


def build_agent(storage_mode: str = "RAM"):
    """创建智能体。

    Args:
        storage_mode: 会话记录存储方式
            "RAM" 用内存（进程退出即丢失）；
            "Sqlite" 持久化到本地数据库（settings.db_path）。
    """
    # 会话记录保存
    # 注意：原来这里先把 InMemorySaver() 和 init_sqlite() 都算出来放进
    # 字典，等于无论选哪种都会去建一次 sqlite 连接；现在改成按需创建。
    if storage_mode == "RAM":
        checkpointer = InMemorySaver()
    elif storage_mode == "Sqlite":
        checkpointer = init_sqlite()
    else:
        # !r 就是输出带引号
        raise ValueError(f"未知的存储类型：{storage_mode!r}（可选 'RAM' / 'Sqlite'）")

    # 初始化中间件
    middleware = SummarizationMiddleware(
        model=summary_model,
        trigger=("tokens", settings.summary_trigger_tokens),  # 触发机制，当 token 超过6000时进行总结
        keep=("messages", settings.summary_keep_messages),
    )

    # 提示词
    system_prompt = load_prompt_template("enterprise_inquiry")

    # 创建智能体
    main_agent = create_agent(
        model=main_llm,
        system_prompt=system_prompt,
        tools=TOOLS,
        middleware=[middleware],
        # checkpointer=checkpointer,
    )

    return main_agent

test_agent = build_agent(storage_mode="RAM")