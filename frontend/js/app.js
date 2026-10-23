/* 星鉴 · 前端逻辑 */
(() => {
  "use strict";

  // 后端查询接口地址。
  // 前端由 app/server.py 同源托管时，用相对路径即可；
  // 若前端单独部署，请改成后端的完整地址，例如 "http://127.0.0.1:8000/api/query"。
  const API_ENDPOINT = "/api/query";

  const els = {
    form: document.getElementById("search-form"),
    input: document.getElementById("search-input"),
    chips: document.getElementById("chips"),
    empty: document.getElementById("state-empty"),
    loading: document.getElementById("state-loading"),
    loadingText: document.getElementById("loading-text"),
    error: document.getElementById("state-error"),
    errorText: document.getElementById("error-text"),
    resultBox: document.getElementById("result-box"),
    report: document.getElementById("report"),
    copyBtn: document.getElementById("btn-copy"),
  };

  const LOADING_MESSAGES = [
    "正在检索公开信息…",
    "正在整理工商信息…",
    "正在分析股权结构…",
    "正在汇总经营与财务状况…",
    "正在核对风险与司法信息…",
    "正在梳理知识产权与资质…",
    "正在生成调研报告…",
  ];
  let loadingTimer = null;

  // 显隐控制：同时设置 hidden 属性 + 内联 style.display。
  // 内联样式优先级最高，任何 CSS（包括被缓存的旧 CSS）都无法覆盖。
  function setVisible(el, visible, display) {
    el.hidden = !visible;
    el.style.display = visible ? display : "none";
  }

  function show(state) {
    setVisible(els.empty, state === "empty", "flex");
    setVisible(els.loading, state === "loading", "flex");
    setVisible(els.error, state === "error", "flex");
    setVisible(els.resultBox, state === "result", "block");
    if (state === "loading") startLoadingText();
    else stopLoadingText();
  }

  function startLoadingText() {
    let i = 0;
    els.loadingText.textContent = LOADING_MESSAGES[0];
    loadingTimer = setInterval(() => {
      i = (i + 1) % LOADING_MESSAGES.length;
      els.loadingText.textContent = LOADING_MESSAGES[i];
    }, 1800);
  }

  function stopLoadingText() {
    if (loadingTimer) {
      clearInterval(loadingTimer);
      loadingTimer = null;
    }
  }

  function setError(msg) {
    els.errorText.textContent = msg || "查询失败，请稍后重试。";
    show("error");
  }

  async function query(name) {
    const res = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: name, thread_id: "web-" + Date.now() }),
    });
    let data = null;
    try { data = await res.json(); } catch (_) { /* 非 JSON 响应 */ }
    if (!res.ok || !data || data.ok !== true) {
      const msg = data && (data.detail || data.error);
      throw new Error(msg || "请求失败（HTTP " + res.status + "）");
    }
    return data;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const name = els.input.value.trim();
    if (!name) { els.input.focus(); return; }
    show("loading");
    try {
      const data = await query(name);
      renderMarkdownContent(data.content);
      show("result");
      els.resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      setError(
        err.message +
        "。请确认后端已启动（在项目根目录执行 uv run uvicorn app.server:app --reload），且 .env 已配置密钥。"
      );
    }
  }

  /* ---------- Markdown 渲染 ---------- */

  function renderMarkdownContent(text) {
    els.report.dataset.raw = text;
    els.report.replaceChildren(renderMarkdown(text));
  }

  function renderMarkdown(text) {
    const lines = String(text).replace(/\r\n?/g, "\n").split("\n");
    const frag = document.createDocumentFragment();
    let para = [];
    let i = 0;

    const flushPara = () => {
      if (!para.length) return;
      const p = document.createElement("p");
      para.forEach((line, idx) => {
        if (idx) p.appendChild(document.createElement("br"));
        appendInline(p, line);
      });
      frag.appendChild(p);
      para = [];
    };

    while (i < lines.length) {
      const line = lines[i];
      const t = line.trim();

      // 代码块 ```
      if (t.startsWith("```")) {
        flushPara();
        const lang = t.slice(3).trim();
        const codeLines = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith("```")) {
          codeLines.push(lines[i]);
          i++;
        }
        i++; // 跳过结束的 ```
        const pre = document.createElement("pre");
        const code = document.createElement("code");
        code.textContent = codeLines.join("\n");
        if (lang) code.className = "language-" + lang;
        pre.appendChild(code);
        frag.appendChild(pre);
        continue;
      }

      // 标题
      const h = t.match(/^(#{1,6})\s+(.+)$/);
      if (h) {
        flushPara();
        const el = document.createElement("h" + h[1].length);
        appendInline(el, h[2]);
        frag.appendChild(el);
        i++;
        continue;
      }

      // 分隔线
      if (/^(-{3,}|\*{3,}|_{3,})$/.test(t)) {
        flushPara();
        frag.appendChild(document.createElement("hr"));
        i++;
        continue;
      }

      // 引用
      if (t.startsWith(">")) {
        flushPara();
        const bq = document.createElement("blockquote");
        const q = [];
        while (i < lines.length && lines[i].trim().startsWith(">")) {
          q.push(lines[i].trim().replace(/^>\s?/, ""));
          i++;
        }
        const p = document.createElement("p");
        q.forEach((l, idx) => {
          if (idx) p.appendChild(document.createElement("br"));
          appendInline(p, l);
        });
        bq.appendChild(p);
        frag.appendChild(bq);
        continue;
      }

      // 表格（GFM）：表头行 + |---|---| 分隔行 + 若干数据行
      if (t.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
        flushPara();
        const header = splitTableRow(t);
        const aligns = splitTableRow(lines[i + 1]).map(cellAlign);
        i += 2;
        const rows = [];
        while (i < lines.length) {
          const rowLine = lines[i].trim();
          // 空行、或不再包含竖线的行，视为表格结束
          if (!rowLine || !rowLine.includes("|") || isTableSeparator(rowLine)) break;
          rows.push(splitTableRow(rowLine));
          i++;
        }
        frag.appendChild(buildTable(header, aligns, rows));
        continue;
      }

      // 列表
      if (/^([-*+]|\d+[.)])\s+/.test(t)) {
        flushPara();
        const ordered = /^\d+[.)]\s+/.test(t);
        const list = document.createElement(ordered ? "ol" : "ul");
        while (i < lines.length) {
          const m = lines[i].trim().match(/^([-*+]|\d+[.)])\s+(.*)$/);
          if (!m) break;
          const li = document.createElement("li");
          appendInline(li, m[2]);
          list.appendChild(li);
          i++;
        }
        frag.appendChild(list);
        continue;
      }

      // 空行 → 分段
      if (!t) {
        flushPara();
        i++;
        continue;
      }

      // 章节标题（agent 结构化输出里的【...】）
      const sec = t.match(/^【(.+?)】$/);
      if (sec) {
        flushPara();
        const el = document.createElement("h3");
        el.className = "report__section-title";
        el.textContent = sec[1];
        frag.appendChild(el);
        i++;
        continue;
      }

      // 普通文本
      para.push(line);
      i++;
    }
    flushPara();
    return frag;
  }

  /* 表格：把 `| a | b |` 拆成单元格；支持 \| 转义。 */
  function splitTableRow(line) {
    let s = String(line).trim();
    if (s.startsWith("|")) s = s.slice(1);
    if (s.endsWith("|")) s = s.slice(0, -1);
    const cells = [];
    let cur = "";
    for (let k = 0; k < s.length; k++) {
      if (s[k] === "\\" && s[k + 1] === "|") { cur += "|"; k++; continue; }
      if (s[k] === "|") { cells.push(cur.trim()); cur = ""; continue; }
      cur += s[k];
    }
    cells.push(cur.trim());
    return cells;
  }

  /* 分隔行：`|---|:---:|`，三种对齐写法都要认。 */
  function isTableSeparator(line) {
    const s = String(line).trim();
    if (!s.includes("|") || !s.includes("-")) return false;
    const cells = splitTableRow(s);
    return cells.length > 0 && cells.every((cell) => /^:?-+:?$/.test(cell));
  }

  function cellAlign(cell) {
    const s = String(cell).trim();
    const left = s.startsWith(":");
    const right = s.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    if (left) return "left";
    return "";
  }

  function buildTable(header, aligns, rows) {
    // 宽表格在窄屏上横向滚动，不撑破结果框
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    const table = document.createElement("table");

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    header.forEach((cell, idx) => {
      const th = document.createElement("th");
      if (aligns[idx]) th.style.textAlign = aligns[idx];
      appendInline(th, cell);
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    if (rows.length) {
      const tbody = document.createElement("tbody");
      rows.forEach((cells) => {
        const tr = document.createElement("tr");
        for (let idx = 0; idx < header.length; idx++) {
          const td = document.createElement("td");
          if (aligns[idx]) td.style.textAlign = aligns[idx];
          appendInline(td, cells[idx] || "");
          tr.appendChild(td);
        }
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }

    wrap.appendChild(table);
    return wrap;
  }

  // 安全地渲染行内文本：支持 [链接](url)、**粗体**、`代码`、*斜体*，不注入 HTML。
  function appendInline(parent, text) {
    const s = String(text);
    const re = /(\[([^\]]+)\]\(([^)\s]+)\))|(\*\*([^*]+)\*\*)|(`([^`]+)`)|(\*([^*]+)\*)/g;
    let last = 0;
    let m;
    while ((m = re.exec(s)) !== null) {
      if (m.index > last) parent.appendChild(document.createTextNode(s.slice(last, m.index)));
      if (m[1] !== undefined) {
        const url = m[3];
        if (/^(https?:\/\/|mailto:|\/|#|\.)/i.test(url)) {
          const a = document.createElement("a");
          a.href = url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          appendInline(a, m[2]);
          parent.appendChild(a);
        } else {
          parent.appendChild(document.createTextNode(m[1]));
        }
      } else if (m[4] !== undefined) {
        const strong = document.createElement("strong");
        appendInline(strong, m[5]);
        parent.appendChild(strong);
      } else if (m[6] !== undefined) {
        const code = document.createElement("code");
        code.textContent = m[7];
        parent.appendChild(code);
      } else if (m[8] !== undefined) {
        const em = document.createElement("em");
        appendInline(em, m[9]);
        parent.appendChild(em);
      }
      last = re.lastIndex;
    }
    if (last < s.length) parent.appendChild(document.createTextNode(s.slice(last)));
  }

  /* ---------- 事件绑定 ---------- */
  els.form.addEventListener("submit", handleSubmit);
  els.chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    els.input.value = chip.dataset.q;
    els.form.requestSubmit();
  });

  els.copyBtn.addEventListener("click", () => {
    const text = els.report.dataset.raw || "";
    if (!text) return;
    navigator.clipboard
      .writeText(text)
      .then(() => {
        els.copyBtn.textContent = "已复制";
        setTimeout(() => { els.copyBtn.textContent = "复制"; }, 1500);
      })
      .catch(() => alert("复制失败，请手动选择复制。"));
  });

  // 页面加载即初始化为「空状态」，确保加载/错误状态一开始就被内联样式隐藏
  show("empty");
})();
