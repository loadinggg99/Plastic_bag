"""企业调研 Agent 实现包。

`app/` 是后端项目根（pyproject / uv.lock / .venv / .env 都在这里），
业务代码拆成两个顶层包：`agent`（Agent 逻辑）和 `server`（FastAPI 服务）。

- `agent.Star_identification_v3`  Agent 创建入口
- `agent.config`                  配置与结构化输出模型
- `agent.prompts`                 Prompt 加载
- `agent.tools`                   六个域的工具
- `agent.resources`               运行时资源（数据库、日志、提示词模板）

Agent 入口：``from agent.Star_identification_v3 import build_agent``。
"""
