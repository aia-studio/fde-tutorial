/* 单步执行：代码行高亮 + 调用栈 + 局部变量（同一对象同一色）。
 *
 * 数据来自 POST /api/trace（服务端 sys.settrace 采集），前端只做回放：
 * 不请求第二次，拖动/回退零延迟。
 */

import { postJSON } from "./api.js";

const PALETTE = [
  "#4d8bf0", "#46c07a", "#e0a33e", "#e2685f", "#a06bf0",
  "#35b9a6", "#e07aa3", "#8b95f0", "#c0a346", "#6bb3e0",
];

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function esc(text) {
  return String(text).replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[ch]);
}

function oidColor(oid) {
  let hash = 0;
  const s = String(oid);
  for (let i = 0; i < s.length; i += 1) hash = (hash * 31 + s.charCodeAt(i)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

/* 值渲染：标量直接显示；容器展开两层；oid 相同的变量在名字旁挂同一色块。 */
function renderValue(value, depth = 0) {
  if (!value) return "";
  const span = el("span", "v-" + (value.t || "?"));

  if (value.oid !== undefined && value.oid !== null) {
    const chip = el("span", "v-oid");
    chip.style.background = oidColor(value.oid);
    chip.title = "同一个对象（引用）";
    span.append(chip);
  }

  if (value.q) {
    span.append(el("span", "v-quote", '"'));
    span.append(el("span", "", value.v));
    span.append(el("span", "v-quote", '"'));
    return span;
  }

  if (Array.isArray(value.items)) {
    const open = value.t === "dict" ? "{" : value.t === "tuple" ? "(" : "[";
    const close = value.t === "dict" ? "}" : value.t === "tuple" ? ")" : "]";
    span.append(el("span", "v-bracket", open));
    value.items.forEach((item, i) => {
      if (i > 0) span.append(el("span", "v-comma", ", "));
      if (value.t === "dict") {
        span.append(renderValue(item[0], depth + 1));
        span.append(el("span", "v-comma", ": "));
        span.append(renderValue(item[1], depth + 1));
      } else {
        span.append(renderValue(item, depth + 1));
      }
    });
    span.append(el("span", "v-bracket", close));
    return span;
  }

  if (value.attrs) {
    span.append(el("span", "v-type", value.t));
    const body = el("span", "v-attrs");
    Object.entries(value.attrs).forEach(([key, val], i) => {
      if (i > 0) body.append(el("span", "v-comma", ", "));
      body.append(el("span", "v-key", key));
      body.append(el("span", "v-comma", "="));
      body.append(renderValue(val, depth + 1));
    });
    span.append(el("span", "v-bracket", "("));
    span.append(body);
    span.append(el("span", "v-bracket", ")"));
    return span;
  }

  if (value.v !== undefined) {
    span.append(el("span", "", value.v));
    if (value.t !== "int" && value.t !== "float" && value.t !== "bool" && value.t !== "NoneType" && value.t !== "callable") {
      const t = el("span", "v-typetag", value.t);
      span.append(t);
    }
  }
  return span;
}

export function createStepper(block, index) {
  const root = el("div", "stepper");
  root.dataset.stepIndex = String(index || 0);
  root.id = `step-${index || 0}`; // 允许用 #/lesson/<id>/step-1 直接定位

  if (block.title) {
    const title = el("div", "st-title");
    title.innerHTML = block.title;
    root.append(title);
  }

  const toolbar = el("div", "st-toolbar");
  const play = el("button", "cb-btn primary", "▶ 运行");
  const prev = el("button", "cb-btn", "◀ 上一步");
  const next = el("button", "cb-btn", "▶ 下一步");
  const end = el("button", "cb-btn", "⏭ 结束");
  const reset = el("button", "cb-btn", "重置");
  const counter = el("span", "st-counter", "点击运行开始追踪");
  prev.disabled = next.disabled = end.disabled = reset.disabled = true;
  toolbar.append(play, prev, next, end, reset, counter);
  root.append(toolbar);

  const body = el("div", "st-body");
  const codePane = el("div", "st-code");
  const panelPane = el("div", "st-panels");
  body.append(codePane, panelPane);
  root.append(body);

  const stackBox = el("div", "st-stack");
  const localsBox = el("div", "st-locals");
  const errorBox = el("div", "st-error");
  errorBox.hidden = true;
  panelPane.append(stackBox, localsBox, errorBox);

  let steps = [];
  let cursor = -1;
  let playing = false;
  let timer = null;
  let loaded = false;
  let stdout = "";

  const stdoutBox = el("div", "st-stdout");
  stdoutBox.hidden = true;
  panelPane.append(stdoutBox);

  const codeLines = block.code.split("\n");
  codeLines.forEach((line, i) => {
    const row = el("div", "st-line", i + 1);
    row.dataset.line = String(i + 1);
    row.textContent = line || " ";
    codePane.append(row);
  });

  const highlight = () => {
    const step = steps[cursor];
    if (!step) return;
    [...codePane.children].forEach((row) => {
      row.classList.toggle("current", Number(row.dataset.line) === step.line);
    });
  };

  const renderFrame = (step) => {
    stackBox.innerHTML = "";
    const label = el("div", "st-label", "调用栈");
    stackBox.append(label);
    const chain = el("div", "st-chain");
    step.stack.forEach((name, i) => {
      const node = el("span", "st-frame" + (i === step.stack.length - 1 ? " top" : ""), name);
      chain.append(node);
      if (i < step.stack.length - 1) chain.append(el("span", "st-arrow", "→"));
    });
    stackBox.append(chain);

    localsBox.innerHTML = "";
    const label2 = el("div", "st-label", "局部变量");
    localsBox.append(label2);

    const names = Object.keys(step.locals || {});
    if (!names.length) {
      localsBox.append(el("div", "st-empty", "（这一帧还没有变量）"));
      return;
    }
    for (const name of names) {
      const row = el("div", "st-var");
      row.append(el("span", "st-var-name", name));
      row.append(el("span", "st-var-eq", "="));
      row.append(renderValue(step.locals[name]));
      localsBox.append(row);
    }
  };

  const renderStep = (i) => {
    const step = steps[i];
    if (!step) return;
    highlight();
    renderFrame(step);
    counter.textContent = `第 ${step.i} / ${steps.length} 步${step.event === "return" ? " · 返回" : ""}`;
    if (step.exc) {
      errorBox.hidden = false;
      errorBox.textContent = step.exc;
    } else {
      errorBox.hidden = true;
    }
    stdoutBox.hidden = !(stdout && i === steps.length - 1);
    if (stdout) stdoutBox.textContent = `程序输出：${stdout.trim()}`;
    const currentRow = codePane.querySelector(".current");
    if (currentRow) currentRow.scrollIntoView({ block: "nearest" });
  };

  const move = (delta) => {
    const nextCursor = Math.min(Math.max(cursor + delta, 0), steps.length - 1);
    if (nextCursor === cursor) return;
    cursor = nextCursor;
    renderStep(cursor);
  };

  const stopPlay = () => {
    playing = false;
    clearInterval(timer);
    play.textContent = "▶ 播放";
  };

  const startPlay = () => {
    if (playing) {
      stopPlay();
      return;
    }
    playing = true;
    play.textContent = "⏸ 暂停";
    timer = setInterval(() => {
      if (cursor >= steps.length - 1) {
        stopPlay();
        return;
      }
      move(1);
    }, 700);
  };

  const enable = (on) => {
    prev.disabled = next.disabled = end.disabled = reset.disabled = !on;
  };

  const load = async () => {
    if (loaded || busy(play)) return;
    play.disabled = true;
    counter.textContent = "追踪中…";
    try {
      const data = await postJSON("/api/trace", { code: block.code });
      if (!data.steps?.length) {
        counter.textContent = "没有可追踪的步骤";
        if (data.error) {
          errorBox.hidden = false;
          errorBox.textContent = data.error;
        }
        return;
      }
      steps = data.steps;
      stdout = data.stdout || "";
      loaded = true;
      enable(true);
      cursor = 0;
      renderStep(0);
      startPlay();
    } catch (err) {
      counter.textContent = String(err.message || err);
    } finally {
      play.disabled = false;
    }
  };

  const busy = (node) => node.disabled;

  play.addEventListener("click", () => (loaded ? startPlay() : load()));
  prev.addEventListener("click", () => { stopPlay(); move(-1); });
  next.addEventListener("click", () => { stopPlay(); move(1); });
  end.addEventListener("click", () => { stopPlay(); cursor = steps.length - 1; renderStep(cursor); });
  reset.addEventListener("click", () => { stopPlay(); cursor = 0; renderStep(0); });

  return root;
}
