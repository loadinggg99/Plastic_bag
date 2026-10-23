"""企业调研 Agent 实现包。

`app` 只作为包命名空间，全部业务代码都收在 `app.agent` 下：

- `app.agent.Star_identification_v2`  Agent 创建入口
- `app.agent.config`                  配置与结构化输出模型
- `app.agent.prompts`                 Prompt 加载
- `app.agent.tools`                   六个域的工具
- `app.agent.resources`               运行时资源（数据库、日志、提示词模板）

Agent 入口：``from app.agent.Star_identification_v2 import build_agent``。
"""
