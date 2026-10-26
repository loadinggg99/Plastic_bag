"""命令行交互入口。

用法（在 app/ 下）：uv run python -m agent.test
输入 exit / quit 退出。
"""
import sys
from pathlib import Path

if __package__ in (None, ""):   # 支持 python agent/test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from agent.main_agent import build_agent


def print_answer(result) -> None:
    """打印本轮回答。

    模型可能先输出一段调用工具前的"预告"，与 tool_calls 同属一条 AIMessage；
    消息列表最后一条才是最终回答。
    """
    print(result["messages"][-1].content)


def main() -> None:
    agent = build_agent("RAM")
    config: RunnableConfig = {"configurable": {"thread_id": "test_01"}}

    print(
        "\n您好，我是你的企业调研助手，我可以帮您查询基础工商信息、人员与股权结构、"
        "经营与财务状况、风险与司法信息、知识产权与资质、经营状况与舆情等相关信息\n"
    )

    while True:
        try:
            human_input = input("你：")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if human_input.strip().lower() in ("exit", "quit"):
            break

        print("  · 正在调研，请稍候…", flush=True)
        result = agent.invoke(
            {"messages": [HumanMessage(content=human_input)]},
            config=config,
        )
        print_answer(result)
        print()


if __name__ == "__main__":
    main()
