# 星鉴 · 前端

星鉴（企业信息查询）的前端页面。包含一个搜索框，输入企业名称后调用后端 Agent，
把返回的 Markdown 文本渲染在搜索框下方的大框里。

## 目录结构

```text
frontend/
├── index.html        # 单页入口
├── css/
│   └── style.css     # 样式（响应式）
├── js/
│   └── app.js        # 请求后端 + 渲染 Markdown + 状态处理
├── assets/
│   └── logo.svg      # 星鉴图标（放大镜 + 五角星）
└── README.md
```

## 快速开始

后端服务在 `app/server/`（FastAPI 包，负责托管本页面 + 调用 Agent）。在 **`app/` 目录**（后端 uv 项目根）执行：

```bash
uv run uvicorn server:app --reload
# 或
uv run python -m server.main
```

然后浏览器打开 <http://127.0.0.1:8000>，接口文档见 <http://127.0.0.1:8000/docs>。

> 首次启动前请确认 `app/.env` 已配置 `DEEPSEEK_API_KEY` 和 `TAVILY_API_KEY`。

## 前后端接口契约

前端向后端 `POST /api/query` 发起查询：

```jsonc
// 请求
{ "query": "深圳市腾讯计算机系统有限公司", "thread_id": "web-169... " }

// 成功响应
{ "ok": true, "content": "【基础工商信息】\n企业名称：…\n……", "company": "腾讯" }

// 失败响应（FastAPI 的 HTTPException）
{ "detail": "错误信息" }
```

前端只依赖 `content`（Agent 返回的文本），直接按 Markdown 渲染显示。

### 如果前端单独部署

前端默认用相对路径 `/api/query` 请求（与 `app/server.py` 同源）。
若前端与后端分开部署，请修改 `js/app.js` 顶部的 `API_ENDPOINT`，改成后端完整地址即可：

```js
const API_ENDPOINT = "http://127.0.0.1:8000/api/query";
```

## 渲染说明

Agent 返回的文本会按 Markdown 渲染，显示在搜索框下方的大框里：

- `#` 到 `######` → 标题
- `**粗体**`、`*斜体*`、`代码`、`[链接](url)` → 行内格式
- `-` 或 `1.` → 列表；三个反引号围起来 → 代码块；`>` → 引用；`---` → 分隔线
- `| 表头 | 表头 |` + `|---|---|` → 表格（支持 `:---` / `:---:` / `---:` 对齐，宽表横向滚动）
- `【标题】` → 章节标题（兼容 agent 当前的结构化输出）

> 渲染器是零依赖的手写实现，只支持上述常用语法；模型若输出任务列表、删除线等
> 更冷门的 GFM 语法，仍会按普通文本显示。需要完整支持时可换成 marked + DOMPurify。
