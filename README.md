# 企业查询 Agent

一个基于 LangGraph + Tavily + DeepSeek 的企业调研 Agent。
用户输入公司名称，Agent 自动调用工具，从公开网络信息中提取并结构化输出企业的六个维度信息：
基础工商信息、人员与股权结构、经营与财务状况、风险与司法信息、知识产权与资质、经营状况与舆情。

> 仅查询合法公开信息，不涉及任何隐私数据。

---

## ✨ 功能

| 工具                               | 文件                                              | 负责内容                                                           |
| -------------------------------- | ----------------------------------------------- | -------------------------------------------------------------- |
| `get_basic_business_info`        | `app/agent/tools/basic_business_info.py`        | 名称/曾用名、各类代码、法定代表人、注册资本、成立日期、营业期限、经营状态、企业类型、注册地址、经营范围、登记机关、所属行业 |
| `get_personnel_equity_structure` | `app/agent/tools/personnel_equity_structure.py` | 主要人员（高管）、股东信息、最终受益人、实际控制人、股权穿透图/企业关系图谱                         |
| `get_business_financial_status`  | `app/agent/tools/business_financial_status.py`  | 财务数据、上市信息、对外投资、分支机构、融资历史、企业年报、招投标                              |
| `get_risk_judicial_info`         | `app/agent/tools/risk_judicial_info.py`         | 司法风险、执行信息、经营风险、税务风险、破产重整                                       |
| `get_ip_qualification`           | `app/agent/tools/ip_qualification.py`           | 商标、专利、著作权、软件著作权、资质证书、网站备案                                      |
| `get_operation_public_opinion`   | `app/agent/tools/operation_public_opinion.py`   | 员工规模、招聘信息、新闻舆情、企业评分                                            |

每个工具内部流程一致：

1. 用 Tavily 搜相关关键词（覆盖面大的域会搜两路：如「人员与股东」「股权穿透与实控人」，两路结果拼成一份材料）
2. 用结构化 LLM 提取字段（`app/agent/tools/__init__.py` 里的 `extract_structured()` 统一封装）
3. 用 `collect_urls()` 从 Tavily 原始返回值里收集真实链接，回填到 `source_url`（不经过 LLM，避免编造）
4. 返回 `to_display()` 生成的格式化文本，每个板块末尾都有一行「数据来源URL」

查询结果页会把六个板块排成 **3 列 × 2 行** 的网格，铺满内容区。每个板块是一张独立卡片，卡片底部按钮带有该领域的 SVG 图标；点击按钮会跳转到 `/report/{report_id}/{section_key}` 这一独立详情页，由 FastAPI + Jinja2 服务端渲染。

- 六个板块固定按「基础工商信息 → 人员与股权结构 → 经营与财务状况 → 风险与司法信息 → 知识产权与资质 → 经营状况与舆情」排列，模型输出顺序变化也不会乱。
- 本次没有查询到的板块仍会显示卡片，但按钮置灰为「本次未查询」。
- 没有按【板块名】输出的内容会保留一个「查看完整内容」入口，不会丢信息。

---

## 📁 项目结构

```text
Star_identification_v3/
├── app/                            # 后端，同时是 uv 项目根（venv/依赖/配置都在这一层）
│   ├── .venv/                      # 虚拟环境（不提交）
│   ├── .env                        # 环境变量（不提交！）
│   ├── .python-version             # 固定 Python 3.14
│   ├── pyproject.toml              # 依赖、uv 源、fastapi 入口
│   ├── uv.lock                     # 锁定版本
│   ├── requirements.txt            # pip freeze 快照（不含项目自身）
│   ├── langgraph.json              # langgraph dev 配置
│   ├── agent/                      # Agent 全部实现（顶层包 agent）
│   │   ├── __init__.py             # 包说明与模块导航
│   │   ├── Star_identification_v2.py   # Agent 创建入口（build_agent / test_agent）
│   │   ├── config/
│   │   │   ├── __init__.py             # 统一出口：settings / dbConfig / 输出模型
│   │   │   ├── basic_config.py         # 基础配置（模型、路径、Tavily 参数）
│   │   │   ├── database_config.py      # 数据库配置
│   │   │   └── output_config.py        # Pydantic 输出模型
│   │   ├── prompts/
│   │   │   └── prompt.py               # Prompt 加载逻辑
│   │   ├── tools/
│   │   │   ├── basic_business_info.py        # 基础工商信息工具
│   │   │   ├── personnel_equity_structure.py # 人员与股权结构工具
│   │   │   ├── business_financial_status.py  # 经营与财务状况工具
│   │   │   ├── risk_judicial_info.py         # 风险与司法信息工具
│   │   │   ├── ip_qualification.py           # 知识产权与资质工具
│   │   │   ├── operation_public_opinion.py   # 经营状况与舆情工具
│   │   │   ├── __init__.py                   # 工具包出口 + extract_structured 公共抽取
│   │   │   └── tavily_client.py              # Tavily 统一封装
│   │   ├── resources/                  # 运行时资源
│   │   │   ├── db/                      # sqlite 数据库（.db 文件专用）
│   │   │   │   └── checkpoint.db        # 会话记录，首次用 Sqlite 时自动创建
│   │   │   ├── logs/                    # 日志
│   │   │   └── prompts/
│   │   │       └── enterprise_inquiry.yaml   # Prompt 模板
│   │   ├── database.py                 # SQLite checkpointer
│   │   ├── llm.py                       # LLM 实例 + 结构化 LLM
│   │   └── test.py                      # 命令行交互入口
│   └── server/                     # FastAPI 服务 + 服务端渲染（顶层包 server）
│       ├── __init__.py                 # create_app：中间件、路由、静态白名单
│       ├── main.py                     # uvicorn 启动入口
│       ├── dependencies.py             # agent 单例与调用封装
│       ├── security.py                 # CSP / 安全响应头
│       ├── sections.py                 # 六板块元数据、SVG 图标、解析与安全 HTML 渲染
│       ├── report_store.py             # 内存报告缓存（TTL + 容量上限）
│       ├── config/
│       │   └── settings.py             # host/port/模板目录/报告缓存配置
│       ├── routes/
│       │   ├── query.py                # POST /api/query
│       │   └── pages.py                # GET /report/{id} 与 /report/{id}/{section}
│       └── templates/
│           ├── base.html               # 公共布局
│           ├── report.html             # 2×3 板块网格
│           ├── section.html            # 板块详情页
│           └── error.html              # 报告过期 / 板块不存在
├── frontend/                       # 首页静态资源（搜索 → 跳转报告页）
├── tests/                          # pytest 测试
├── conftest.py                     # 测试期的 sys.path 与假密钥兜底
├── pytest.ini                      # pytest 配置（pythonpath = app）
├── README.md
└── .gitignore
```

> `app/` 是后端项目根：`agent/` 放 Agent 逻辑，`server/` 放 FastAPI 服务与 Jinja2 模板；导入路径统一为 `agent.*` / `server.*`。

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+（本项目锁定 3.14）
- 推荐使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖

### 2. 安装依赖

后端是独立的 uv 项目，项目根在 `app/`（`.venv`、`uv.lock` 都跟着它走）：

```bash
cd app
uv sync
```

### 3. 配置环境变量

在 `app/` 下创建 `.env`（配置里用 `__file__` 算出绝对路径 `app/.env`，不随工作目录漂移）：

```env
TAVILY_API_KEY=tvly-xxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 4. 运行

以下命令都在 `app/` 下执行：

```bash
cd app

uv run python -m agent.test          # 交互式对话
uv run uvicorn server:app --reload   # Web 服务（页面在仓库根的 frontend/）
uv run langgraph dev                 # LangGraph 本地服务 / Studio
```

输入 `exit` 或 `quit` 退出交互对话。

作为库调用（在 `app/` 下）：

```python
from agent.Star_identification_v2 import build_agent

agent = build_agent()  # 默认 "RAM"，会话存在内存里
# agent = build_agent("Sqlite")  # 持久化到 app/agent/resources/db/checkpoint.db

result = agent.invoke(
  {"messages": [("user", "帮我调研一下某某公司的基本情况")]},
  config={"configurable": {"thread_id": "demo"}},
)
print(result["messages"][-1].content)
```

### 5. 测试

`tests/` 留在仓库根，后端依赖在 `app/.venv`，所以用 `--project app` 指定项目根：

```bash
# 在仓库根执行
uv run --project app pytest                                         # 离线测试，不需要网络和 key
RUN_LIVE_TESTS=1 uv run --project app pytest tests/test_live_e2e.py -v -s   # 联网端到端（会真实调用 API）
```

也可以在 `app/` 下执行 `uv run pytest ../tests`，效果相同。

---

## 🧠 核心设计

- **LLM 统一管理**（`app/agent/llm.py`）：`main_llm` / `summary_model` / 六个结构化 LLM（`basic_info_llm` / `equity_llm` / `finance_llm` / `risk_llm` / `ip_llm` / `opinion_llm`）都在这里创建。
- **结构化输出**（`app/agent/config/output_config.py`）：一个域一个 Pydantic 模型，`with_structured_output` 把返回值从 `AIMessage` 换成模型实例。
- **数据来源URL 不经过 LLM**：`source_url` 字段用 `SkipJsonSchema` 排除在结构化 schema 之外，模型看不到；真实链接由 `collect_urls()` 从 Tavily 原始结果里收集、`extract_structured()` 回填，因此不会出现模型编造的链接。
- **结果页/详情页由服务端渲染**（`app/server/routes/pages.py` + `app/server/templates/`）：`/report/{id}` 是 3×2 的六板块网格，`/report/{id}/{section}` 是单个板块详情页。首页只负责搜索，拿到 `report_url` 后跳转。
- **报告缓存**（`app/server/report_store.py`）：`/api/query` 把解析后的六个板块写进进程内缓存，报告页和详情页按 `report_id` 读取。默认 TTL 1 小时、最多 200 份，过期或服务重启后需要重新查询。
- **工具职责单一**（`app/agent/tools/`）：工具返回字符串，Agent 直接展示，格式由代码控制，不依赖 LLM 二次排版。
- **统一导入风格**：`app/` 是项目根，顶层包就是 `agent` / `server`，全项目使用 `agent.*` / `server.*` 绝对导入；入口用 `uv run python -m agent.test`（在 `app/` 下，cwd 天然在 `sys.path` 上；在仓库根跑 pytest 时由 `pytest.ini` 的 `pythonpath = app` 补上）。

---

## 🔒 安全防护

- **严格 CSP**（`app/server/security.py`）：前端页面下发 `default-src 'self'`、`script-src 'self'`、`style-src 'self'`、`object-src 'none'`、`base-uri 'none'`、`frame-ancestors 'none'` 等策略，并开启 `require-trusted-types-for 'script'`；支持的浏览器会直接禁掉 `innerHTML` 一类 DOM XSS 注入点。
- **安全响应头**：`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`、`Permissions-Policy`、`Cross-Origin-Opener-Policy`；HTTPS 下额外下发 HSTS。
- **静态资源白名单**：只挂载 `frontend/index.html` 与 `assets/`、`css/`、`js/` 三个目录，不把 `node_modules/`、`package.json`、`dist/` 暴露到同源下，避免同源任意 HTML/JS 成为 XSS 载体。
- **前端只走安全 DOM API**：首页 JS 只用 `textContent` / `createElement`，不使用 `innerHTML`；链接只允许 `http(s)`、`mailto` 和站内相对地址/锚点，`javascript:`、`data:`、`vbscript:`、协议相对（`//evil.com`）和反斜杠写法一律按纯文本展示。
- **服务端渲染同样防 XSS**：详情页内容由 `sections.py` 先 `escape()` 再拼接 HTML，只把合法 http(s) URL 变成链接；Jinja2 模板开启 autoescape，板块标题、公司名、错误信息等动态文本都不会被当作 HTML。
- **文档页单独放行**：`/docs`、`/redoc`、`/openapi.json` 依赖 CDN 和内联脚本，跳过 CSP（其余安全头照常），避免 Swagger UI 白屏。

---

## ⚠️ 注意事项

- **数据来源**：所有信息来自公开网络，不保证权威性和完整性，仅用于前期快速调研。
- **数据来源URL**：每个板块末尾的「数据来源URL」是本次 Tavily 检索到的原始网页链接（按相关性顺序去重，多个用顿号分隔），只用于回溯核对，不代表内容一定准确；没有搜到链接时显示「未查到」。
- **报告链接有时效**：`/report/{report_id}` 依赖 `report_store.py` 的内存缓存，默认保留 1 小时、最多 200 份。过期、服务重启或换 worker 后访问会看到「报告不存在或已过期」，重新查询即可。
- **单进程缓存**：当前缓存是进程内字典。如果以后用多 worker / 多实例部署，需要把 `ReportStore` 换成 Redis/SQLite 等共享存储，否则详情页可能请求到没有该报告的进程。
- **CSP 与同源部署**：CSP 的 `connect-src 'self'` 假设前端和 `/api/query` 同源；报告页 `/report/...` 也由 FastAPI 渲染。如果把前端单独部署到别的域名，需要同时调整 `API_ENDPOINT`、报告跳转地址和 CSP 的 `connect-src`，或者用反向代理把 `/report` 转发到后端。
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
- **sqlite 连接是复用的**：`init_sqlite()` 按数据库路径缓存 `SqliteSaver`，同一个库只开一个连接。因为 `SqliteSaver` 持有的 `sqlite3.Connection` 是非托管资源，如果每次 `build_agent("Sqlite")` 都新开一个，重复调用会持续泄漏文件句柄。需要在同一进程里模拟重启时，先调 `agent.database.close_sqlite()`。
- **CLI 只打印最后一条消息**：模型调用工具前常常先"自言自语"一句，中英文都有，例如 `I'll look up the basic information for XXX.` 或 `我来帮您查询XXX的基本信息。`。这句和 `tool_calls` 属于**同一条 `AIMessage`**，属于中间过程。好在阻塞式调用拿到的是完整消息列表，且**最后一条一定是给用户的回答**，所以 `app/agent/test.py` 直接取 `result["messages"][-1].content` 就行，预告、工具原始输出都不会被打出来。这也是这里用 `invoke()` 而不是 `stream()` 的原因。
- **`.env` 里有真实密钥**：已在 `.gitignore` 中忽略，请勿提交。
