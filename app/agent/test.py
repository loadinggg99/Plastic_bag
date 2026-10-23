# app/agent/test.py
"""命令行交互入口。

运行方式（二选一，都需要在项目根目录下）：
    python -m app.agent.test
    python app/agent/test.py

连续对话，输入 exit 或 quit 退出。
"""
import sys
from pathlib import Path

# 支持直接 `python app/agent/test.py`：此时 sys.path[0] 是 app/agent/ 而不是
# 项目根，补上项目根才能 import app.agent.xxx。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.agent.Star_identification_v2 import build_agent


def print_answer(result) -> None:
    """打印本轮的回答。

    模型调用工具前常常先输出一句"预告"，中英文都有可能，例如
    "I'll look up the basic information for that company."。
    这句和 tool_calls 属于同一条 AIMessage，而消息列表的**最后一条**
    才是给用户看的回答，所以直接取最后一条即可，不用管中间过程。
    """
    print(result["messages"][-1].content)


def main() -> None:
    agent = build_agent()

    # 配置thread_id，记录对话
    dialogue_config: RunnableConfig = {"configurable": {"thread_id": "test_01"}}

    # 删除 thread_id 的所有记录（需要持久化存储时才可用）：
    #   agent = build_agent("Sqlite")
    #   agent.checkpointer.delete_thread("test_01")

    print(
        "\n您好，我是你的企业调研助手，我可以帮您查询基础工商信息、人员与股权结构、"
        "经营与财务状况、风险与司法信息、知识产权与资质、经营状况与舆情等相关信息\n"
    )

    # 循环输入，连续对话
    while True:
        try:
            human_input = input("你：")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        # 当在对话中输入 exit 或者 quit 时退出对话
        if human_input.strip().lower() in ("exit", "quit"):
            break

        print("  · 正在调研，请稍候…", flush=True)
        result = agent.invoke(
            {"messages": [HumanMessage(content=human_input)]},
            config=dialogue_config,
        )
        print_answer(result)
        print()


if __name__ == "__main__":
    main()
