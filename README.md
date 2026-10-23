# 企业查询 Agent

一个基于 LangGraph + Tavily + DeepSeek 的企业调研 Agent。
用户输入公司名称，Agent 自动调用工具，从公开网络信息中提取并结构化输出企业的六个维度信息：
基础工商信息、人员与股权结构、经营与财务状况、风险与司法信息、知识产权与资质、经营状况与舆情。

> 仅查询合法公开信息，不涉及任何隐私数据。

---

## ✨ 功能

| 工具 | 文件 | 负责内容 |
|---|---|---|
| `get_basic_business_info` | `app/agent/tools/basic_business_info.py` | 名称/曾用名、各类代码、法定代表人、注册资本、成立日期、营业期限、经营状态、企业类型、注册地址、经营范围、登记机关、所属行业 |
| `get_personnel_equity_structure` | `app/agent/tools/personnel_equity_structure.py` | 主要人员（高管）、股东信息、最终受益人、实际控制人、股权穿透图/企业关系图谱 |
| `get_business_financial_status` | `app/agent/tools/business_financial_status.py` | 财务数据、上市信息、对外投资、分支机构、融资历史、企业年报、招投标 |
| `get_risk_judicial_info` | `app/agent/tools/risk_judicial_info.py` | 司法风险、执行信息、经营风险、税务风险、破产重整 |
| `get_ip_qualification` | `app/agent/tools/ip_qualification.py` | 商标、专利、著作权、软件著作权、资质证书、网站备案 |
| `get_operation_public_opinion` | `app/agent/tools/operation_public_opinion.py` | 员工规模、招聘信息、新闻舆情、企业评分 |

每个工具内部流程一致：

1. 用 Tavily 搜相关关键词（覆盖面大的域会搜两路：如「人员与股东」「股权穿透与实控人」，两路结果拼成一份材料）
2. 用结构化 LLM 提取字段（`app/agent/tools/__init__.py` 里的 `extract_structured()` 统一封装）
3. 返回 `to_display()` 生成的格式化文本

---

## 📁 项目结构

```text
project3/
├── .venv/                          # 虚拟环境（不提交）
├── app/
│   ├── __init__.py                 # 包根（仅作为命名空间）
│   └── agent/                      # Agent 全部实现
│       ├── __init__.py             # 包说明与模块导航
│       ├── Star_identification_v2.py   # Agent 创建入口（build_agent / test_agent）
│       ├── config/
│       │   ├── __init__.py             # 统一出口：settings / dbConfig / 输出模型
│       │   ├── basic_config.py         # 基础配置（模型、路径、Tavily 参数）
│       │   ├── database_config.py      # 数据库配置
│       │   └── output_config.py        # Pydantic 输出模型
│       ├── prompts/
│       │   └── prompt.py               # Prompt 加载逻辑
│       ├── tools/
│       │   ├── basic_business_info.py        # 基础工商信息工具
│       │   ├── personnel_equity_structure.py # 人员与股权结构工具
│       │   ├── business_financial_status.py  # 经营与财务状况工具
│       │   ├── risk_judicial_info.py         # 风险与司法信息工具
│       │   ├── ip_qualification.py           # 知识产权与资质工具
│       │   ├── operation_public_opinion.py   # 经营状况与舆情工具
│       │   ├── __init__.py                   # 工具包出口 + extract_structured 公共抽取
│       │   └── tavily_client.py              # Tavily 统一封装
│       ├── resources/                  # 运行时资源
│       │   ├── db/                      # sqlite 数据库（.db 文件专用）
│       │   │   └── checkpoint.db        # 会话记录，首次用 Sqlite 时自动创建
│       │   ├── logs/                    # 日志
│       │   └── prompts/
│       │       └── enterprise_inquiry.yaml   # Prompt 模板
│       ├── database.py                 # SQLite checkpointer
│       ├── llm.py                       # LLM 实例 + 结构化 LLM
│       └── test.py                      # 命令行交互入口
├── tests/                           # pytest 测试
├── src/                             # 预留
├── .env                             # 环境变量（不提交！）
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── requirements.txt
└── uv.lock
```

> 重构后 `app/` 只保留包根，所有业务代码、配置、工具与运行时资源都在 `app/agent/` 下，
> 导入路径统一为 `app.agent.*`。

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+（本项目锁定 3.14）
- 推荐使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

在**项目根目录**创建 `.env`（路径是相对项目根解析的，不是相对当前工作目录）：

```env
TAVILY_API_KEY=tvly-xxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 4. 运行

交互式对话（在项目根目录执行，二选一）：

```bash
python -m app.agent.test
python app/agent/test.py
```

输入 `exit` 或 `quit` 退出。

作为库调用：

```python
from app.agent.Star_identification_v2 import build_agent

agent = build_agent()  # 默认 "RAM"，会话存在内存里
# agent = build_agent("Sqlite")  # 持久化到 app/agent/resources/db/checkpoint.db

result = agent.invoke(
  {"messages": [("user", "帮我调研一下某某公司的基本情况")]},
  config={"configurable": {"thread_id": "demo"}},
)
print(result["messages"][-1].content)
```

### 5. 测试

```bash
python -m pytest              # 离线测试，不需要网络和 key
RUN_LIVE_TESTS=1 python -m pytest tests/test_live_e2e.py -v -s   # 联网端到端（会真实调用 API）
```

---

## 🧠 核心设计

- **LLM 统一管理**（`app/agent/llm.py`）：`main_llm` / `summary_model` / 六个结构化 LLM（`basic_info_llm` / `equity_llm` / `finance_llm` / `risk_llm` / `ip_llm` / `opinion_llm`）都在这里创建。
- **结构化输出**（`app/agent/config/output_config.py`）：一个域一个 Pydantic 模型，`with_structured_output` 把返回值从 `AIMessage` 换成模型实例。
- **工具职责单一**（`app/agent/tools/`）：工具返回字符串，Agent 直接展示，格式由代码控制，不依赖 LLM 二次排版。
- **统一导入风格**：全项目使用 `app.agent.*` 绝对导入，入口用 `python -m app.agent.test` 或 `python app/agent/test.py`。

---

## ⚠️ 注意事项

- **数据来源**：所有信息来自公开网络，不保证权威性和完整性，仅用于前期快速调研。
- **隐私边界**：不查询任何个人隐私信息，不涉及非公开数据。
- **法律与风险信息的边界**：`get_risk_judicial_info` 只检索公开的司法风险、执行信息、经营风险、税务风险和破产重整信息，用于快速摸底；结果可能滞后或与官方渠道（国家企业信用信息公示系统、中国执行信息公开网、裁判文书网等）不一致，不能作为尽调结论或法律依据。
- **股权穿透是推算**：`get_personnel_equity_structure` 的最终受益人、实际控制人和穿透层级来自公开股权链条的推算（或第三方平台的穿透结论），可能与官方登记口径不一致，只作线索。
- **一个域一个工具**：六个工具各自绑定一个 `with_structured_output(<模型>)`，模型之间不共用；改字段时改 `app/agent/config/output_config.py` 对应类即可，工具的搜索词和提示词 hint 在同名模块里。
- **结构化输出兼容性**：`with_structured_output` 依赖模型的 function calling 能力，若 DeepSeek 某型号不支持，需退回到手动 JSON prompt 方案。
- **Tavily `max_results` 上限是 20**：取值 1–20，超过 20 服务端不报错但会静默降级（比如传 50 实际只返回 10 条），所以配置里加了 `ge=1, le=20` 校验。
- **资源目录结构**：全部收在 `app/agent/resources/` 下，各管各的：

  | 目录 | 用途 | 是否提交 |
  |---|---|---|
  | `app/agent/resources/db/` | sqlite 数据库（`.db`） | 否，自动创建 |
  | `app/agent/resources/logs/` | 日志 | 否 |
  | `app/agent/resources/prompts/` | prompt 模板 | 是 |

  配置里不写 `"./resources/checkpoint.db"` 这种相对路径，而是基于 `__file__` 算绝对路径。否则路径会跟着当前工作目录漂移（`<根>/resources` 与 `app/agent/resources` 的差别），换个目录启动就找不到数据库了。
- **sqlite 连接是复用的**：`init_sqlite()` 按数据库路径缓存 `SqliteSaver`，同一个库只开一个连接。因为 `SqliteSaver` 持有的 `sqlite3.Connection` 是非托管资源，如果每次 `build_agent("Sqlite")` 都新开一个，重复调用会持续泄漏文件句柄。需要在同一进程里模拟重启时，先调 `app.agent.database.close_sqlite()`。
- **CLI 只打印最后一条消息**：模型调用工具前常常先"自言自语"一句，中英文都有，例如 `I'll look up the basic information for XXX.` 或 `我来帮您查询XXX的基本信息。`。这句和 `tool_calls` 属于**同一条 `AIMessage`**，属于中间过程。好在阻塞式调用拿到的是完整消息列表，且**最后一条一定是给用户的回答**，所以 `app/agent/test.py` 直接取 `result["messages"][-1].content` 就行，预告、工具原始输出都不会被打出来。这也是这里用 `invoke()` 而不是 `stream()` 的原因。
- **`.env` 里有真实密钥**：已在 `.gitignore` 中忽略，请勿提交。
