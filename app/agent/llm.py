from app.agent.config import (
    BasicBusinessInfo,
    BusinessFinancialStatus,
    IpQualification,
    OperationPublicOpinion,
    PersonnelEquityStructure,
    RiskJudicialInfo,
    settings,
)
from langchain_openai import ChatOpenAI

# 主模型
main_llm = ChatOpenAI(
    model=settings.main_model,
    api_key=settings.api_key,
    base_url=settings.base_url,
    temperature=0.7,
)

# 中间件模型
summary_model = ChatOpenAI(
    model=settings.summary_model,
    api_key=settings.summary_model_api_key,
    base_url=settings.summary_model_base_url,
    temperature=0.7,
)

# 结构化输出模型
# 这里刻意用 settings.structured_model（deepseek-chat）而不是 main_model：
# deepseek-flash 是思考模型，实测调用工具时不接受任何 tool_choice
# （required 和指定函数名都会报 400 "Thinking mode does not support this tool_choice"），
# 而 with_structured_output 一定会强制 tool_choice，两者无法共存。
output_llm = ChatOpenAI(
    model=settings.structured_model,
    api_key=settings.api_key,
    base_url=settings.base_url,
    temperature=0,
)

# with_structured_output(BasicBusinessInfo) 做的事是：给 LLM 绑定一个"输出必须符合
# BasicBusinessInfo 结构"的约束。绑定之后，这个 LLM 实例的 invoke() 返回值不再是
# AIMessage，而是对应的 Pydantic 实例（六个域各一个模型，见 output_config.py）。

# 必须显式指定 method="function_calling"：
# langchain-openai >= 0.3 起 with_structured_output 默认走 OpenAI 的 json_schema
# response_format，DeepSeek 不支持，会直接报 400
# "This response_format type is unavailable now"。
# 另一条路 method="json_mode" 也不行，DeepSeek 要求 prompt 里必须出现 "json" 字样。
_STRUCTURED_KWARGS = {"method": "function_calling"}

# 一个域一个结构化 LLM，与 app/agent/tools/ 下的六个工具一一对应
basic_info_llm = output_llm.with_structured_output(BasicBusinessInfo, **_STRUCTURED_KWARGS)
equity_llm = output_llm.with_structured_output(PersonnelEquityStructure, **_STRUCTURED_KWARGS)
finance_llm = output_llm.with_structured_output(BusinessFinancialStatus, **_STRUCTURED_KWARGS)
risk_llm = output_llm.with_structured_output(RiskJudicialInfo, **_STRUCTURED_KWARGS)
ip_llm = output_llm.with_structured_output(IpQualification, **_STRUCTURED_KWARGS)
opinion_llm = output_llm.with_structured_output(OperationPublicOpinion, **_STRUCTURED_KWARGS)
