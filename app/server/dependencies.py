"""共享依赖：agent 单例、并发控制与调用封装。"""
import threading
import time

from langchain_core.messages import HumanMessage

from agent.logger import get_logger
from server.config import settings

logger = get_logger("server.dependencies")

_agent = None
_agent_init_lock = threading.Lock()

# 限制同时执行的查询数：保护上游 API（Tavily / DeepSeek）不被瞬时打爆，
# 同时避免请求堆积时线程与内存被占满。超出的请求在此排队等待。
_agent_semaphore = threading.Semaphore(settings.max_concurrent_queries)


def get_agent():
    """延迟构建 agent（进程内单例，首次访问时初始化）。"""
    global _agent
    if _agent is None:
        with _agent_init_lock:
            if _agent is None:
                logger.info("首次构建 agent（storage_mode=RAM）")
                from agent.main_agent import build_agent

                _agent = build_agent(storage_mode="RAM")
                logger.info("agent 构建完成")
    return _agent


def invoke_agent(query: str, thread_id: str = "web") -> str:
    """把 query 交给 agent 执行，返回最后一条消息的文本。

    最多并发 settings.max_concurrent_queries 个查询，其余排队。
    """
    agent = get_agent()
    logger.info("开始查询：query=%r thread_id=%s", query, thread_id)
    started = time.perf_counter()

    with _agent_semaphore:
        waited = time.perf_counter() - started
        if waited > 0.5:
            logger.info(
                "查询排队 %.2fs 后执行（并发上限 %d）",
                waited,
                settings.max_concurrent_queries,
            )
        run_started = time.perf_counter()
        try:
            result = agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config={"configurable": {"thread_id": thread_id}},
            )
        except Exception:
            logger.exception("查询失败：query=%r thread_id=%s", query, thread_id)
            raise
        ran = time.perf_counter() - run_started

    messages = result["messages"]
    used_tools = {
        call["name"]
        for message in messages
        for call in (getattr(message, "tool_calls", None) or [])
    }
    final = messages[-1]

    logger.info(
        "查询完成：总耗时 %.2fs（排队 %.2fs，执行 %.2fs），消息 %d 条，调用工具 %d 个 %s，结果 %d 字符",
        time.perf_counter() - started,
        waited,
        ran,
        len(messages),
        len(used_tools),
        sorted(used_tools),
        len(str(final.content)),
    )
    if len(used_tools) < 6:
        logger.warning(
            "本次只调用了 %d/6 个域工具，报告页会出现「本次未查询」的板块：%s",
            len(used_tools),
            sorted(used_tools),
        )

    return final.content
