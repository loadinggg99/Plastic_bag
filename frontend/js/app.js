/* 星鉴 · 首页逻辑：搜索 → 请求后端 → 跳转到服务端渲染的报告页 */
(() => {
  "use strict";

  // 后端查询接口地址。前端与后端同源部署时用相对路径即可。
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
    try {
      data = await res.json();
    } catch (_) {
      /* 非 JSON 响应 */
    }

    if (!res.ok || !data || data.ok !== true) {
      const msg = data && (data.detail || data.error);
      throw new Error(msg || "请求失败（HTTP " + res.status + "）");
    }
    return data;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const name = els.input.value.trim();
    if (!name) {
      els.input.focus();
      return;
    }

    show("loading");
    try {
      const data = await query(name);

      // 只允许跳转到本站报告页，避免后端异常时被带到外部地址
      const url = String(data.report_url || "");
      if (!url.startsWith("/report/")) {
        throw new Error("查询成功，但没有返回有效的报告地址");
      }

      stopLoadingText();
      window.location.assign(url);
    } catch (err) {
      setError(
        err.message +
          "。请确认后端已启动（在 app/ 目录执行 uv run uvicorn server:app --reload），且 app/.env 已配置密钥。"
      );
    }
  }

  /* ---------- 事件绑定 ---------- */
  els.form.addEventListener("submit", handleSubmit);
  els.chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    els.input.value = chip.dataset.q;
    els.form.requestSubmit();
  });

  // 页面加载即初始化为「空状态」，确保加载/错误状态一开始就被内联样式隐藏
  show("empty");
})();
