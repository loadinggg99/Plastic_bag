"""LLM 实例。

main_llm / summary_model 用于对话与摘要；output_llm 派生出六个结构化抽取
LLM，with_structured_output 之后 invoke 直接返回对应的 Pydantic 实例。
"""
from agent.config import (
    BasicBusinessInfo,
    BusinessFinancialStatus,
    IpQualification,
    OperationPublicOpinion,
    PersonnelEquityStructure,
    RiskJudicialInfo,
    settings,
)
from langchain_openai import ChatOpenAI

main_llm = ChatOpenAI(
    model=settings.main_model,
    api_key=settings.api_key,
    base_url=settings.base_url,
    temperature=0.7,
)

summary_model = ChatOpenAI(
    model=settings.summary_model,
    api_key=settings.summary_model_api_key,
    base_url=settings.summary_model_base_url,
    temperature=0.7,
)

# 结构化抽取必须用非思考模型：deepseek-flash 会拒绝任何 tool_choice
# （400 "Thinking mode does not support this tool_choice"），而
# with_structured_output 一定会强制 tool_choice。
output_llm = ChatOpenAI(
    model=settings.structured_model,
    api_key=settings.api_key,
    base_url=settings.base_url,
    temperature=0,
)

# DeepSeek 不支持 OpenAI 的 json_schema response_format，只能走 function_calling
_STRUCTURED_KWARGS = {"method": "function_calling"}

basic_info_llm = output_llm.with_structured_output(BasicBusinessInfo, **_STRUCTURED_KWARGS)
equity_llm = output_llm.with_structured_output(PersonnelEquityStructure, **_STRUCTURED_KWARGS)
finance_llm = output_llm.with_structured_output(BusinessFinancialStatus, **_STRUCTURED_KWARGS)
risk_llm = output_llm.with_structured_output(RiskJudicialInfo, **_STRUCTURED_KWARGS)
ip_llm = output_llm.with_structured_output(IpQualification, **_STRUCTURED_KWARGS)
opinion_llm = output_llm.with_structured_output(OperationPublicOpinion, **_STRUCTURED_KWARGS)
