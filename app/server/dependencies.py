# app/server/dependencies.py
"""共享依赖：agent 单例与调用封装。"""
import threading

from langchain_core.messages import HumanMessage

_agent = None
_agent_lock = threading.Lock()


def get_agent():
    """延迟构建 agent（避免导入时就加载模型）。"""
    global _agent
    if _agent is None:
        from app.agent.Star_identification_v2 import build_agent
        _agent = build_agent(storage_mode="RAM")
    return _agent


def invoke_agent(query: str, thread_id: str = "web") -> str:
    """把 query 原样作为 HumanMessage 交给 agent，返回最后一条消息的文本。"""
    agent = get_agent()
    with _agent_lock:
        result = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": thread_id}},
        )
    return result["messages"][-1].content
