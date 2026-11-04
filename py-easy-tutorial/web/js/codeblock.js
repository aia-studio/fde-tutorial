/* 可编辑代码块 + 真实执行面板。
 *
 * 交互契约：Ctrl/Cmd+Enter 运行；运行中按钮变成「停止」；输出实时追加；
 * `input()` 可交互（出现输入行）；出错时给出「第 N 行」并可一键选中。
 */

import { postJSON } from "./api.js";
import { highlightPython } from "./highlight.js";

const INPUT_HINT = /\binput\s*\(/;
const ERROR_LINE = /File "main\.py", line (\d+)/g;

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function createCodeBlock(block, lessonId, options = {}) {
  const root = el("div", "codeblock");

  const top = el("div", "cb-top");
  const lang = el("span", "cb-lang", block.lang || "text");
  top.append(lang, el("span", "sp"));

  if (!block.runnable) {
    const pre = el("pre");
    pre.style.margin = "0";
    pre.style.padding = "13px 14px";
    pre.style.font = "13px/1.65 var(--mono)";
    pre.style.overflow = "auto";
    pre.textContent = block.code;
    root.append(top, pre);
    return root;
  }

  const runBtn = el("button", "cb-btn primary", "运行");
  runBtn.title = "Ctrl / Cmd + Enter";
  const resetBtn = el("button", "cb-btn", "重置");
  top.append(runBtn, resetBtn);

  const editor = el("div", "cb-editor");
  const gutter = el("div", "cb-gutter");
  const wrap = el("div", "cb-codewrap");
  const highlight = el("pre", "cb-highlight");
  highlight.setAttribute("aria-hidden", "true");
  const area = el("textarea", "cb-code");
  area.value = block.code;
  area.spellcheck = false;
  area.setAttribute("aria-label", "可编辑代码");
  wrap.append(highlight, area);
  editor.append(gutter, wrap);

  const stdinRow = el("div", "cb-stdin");
  stdinRow.hidden = true;
  const stdinInput = el("input", "cb-stdin-input");
  stdinInput.type = "text";
  stdinInput.placeholder = "程序在等输入，敲一行后回车";
  stdinInput.setAttribute("aria-label", "标准输入");
  const stdinBtn = el("button", "cb-btn", "发送");
  stdinRow.append(el("span", "cb-stdin-label", "stdin"), stdinInput, stdinBtn);

  const out = el("div", "cb-out");
  out.hidden = true;
  const pre = el("pre");
  const status = el("div", "cb-status");
  status.setAttribute("aria-live", "polite");
  const dot = el("span", "dot");
  const statusText = el("span", "", "就绪");
  const errJump = el("button", "err-jump");
  errJump.hidden = true;
  status.append(dot, statusText, errJump);
  out.append(pre, status);

  root.append(top, editor, stdinRow, out);

  const source = new EventSourceStream();
  let running = false;
  let stderrBuf = "";
  let lastChunkAt = 0;
  let lastChunkOpenLine = false;
  let idleTimer = null;

  const syncGutter = () => {
    const lines = area.value.split("\n").length;
    let text = "";
    for (let i = 1; i <= lines; i += 1) text += i + "\n";
    gutter.textContent = text;
    highlight.innerHTML = highlightPython(area.value) + "\n";
    autoGrow();
  };

  const autoGrow = () => {
    area.style.height = "auto";
    const next = Math.max(area.scrollHeight, 44);
    area.style.height = next + "px";
    gutter.style.minHeight = next + "px";
  };

  const setStatus = (state, text) => {
    status.className = "cb-status" + (state ? " " + state : "");
    statusText.textContent = text;
  };

  const setRunning = (value) => {
    running = value;
    runBtn.textContent = value ? "停止" : "运行";
    runBtn.classList.toggle("danger", value);
    runBtn.classList.toggle("primary", !value);
    if (!value) hideStdin();
  };

  const showStdin = () => {
    if (!running || !stdinRow.hidden) return;
    stdinRow.hidden = false;
    stdinInput.value = "";
    stdinInput.focus();
  };

  const hideStdin = () => {
    stdinRow.hidden = true;
  };

  const append = (text, cls) => {
    out.hidden = false;
    pre.append(el("span", cls || "", text));
    pre.scrollTop = pre.scrollHeight;
  };

  const sendLine = async () => {
    const value = stdinInput.value;
    if (!running) return;
    stdinInput.value = "";
    append(value + "\n", "echo");
    if (!source.runId) return;
    try {
      const res = await postJSON(`/api/run/${source.runId}/stdin`, { data: value });
      if (!res.sent) append("[进程已结束，输入被丢弃]\n", "err");
    } catch (err) {
      append(String(err.message || err) + "\n", "err");
    }
  };

  const reset = () => {
    source.close();
    stopIdleWatch();
    area.value = block.code;
    syncGutter();
    out.hidden = true;
    pre.textContent = "";
    stderrBuf = "";
    errJump.hidden = true;
    setRunning(false);
    setStatus("", "就绪");
  };

  const finish = (data) => {
    setRunning(false);
    stopIdleWatch();
    const ms = data.duration_ms ?? 0;
    if (data.timed_out) {
      setStatus("bad", `超时已终止 · ${ms} ms`);
    } else if (data.exit_code === 0) {
      setStatus("ok", `退出码 0 · ${ms} ms`);
    } else {
      setStatus("bad", `退出码 ${data.exit_code} · ${ms} ms`);
    }
    if (data.truncated) append("\n[输出已截断]\n", "err");
    showErrorLine();
  };

  const showErrorLine = () => {
    const matches = [...stderrBuf.matchAll(ERROR_LINE)];
    if (!matches.length) {
      errJump.hidden = true;
      return;
    }
    const line = Number(matches[matches.length - 1][1]);
    const total = area.value.split("\n").length;
    if (!Number.isFinite(line) || line < 1 || line > total) {
      errJump.hidden = true;
      return;
    }
    errJump.textContent = `错误在第 ${line} 行`;
    errJump.dataset.line = String(line);
    errJump.hidden = false;
  };

  const selectLine = (line) => {
    const lines = area.value.split("\n");
    let start = 0;
    for (let i = 0; i < line - 1 && i < lines.length; i += 1) start += lines[i].length + 1;
    const end = start + (lines[line - 1]?.length ?? 0);
    area.focus();
    area.setSelectionRange(start, end);
  };

  const startIdleWatch = () => {
    stopIdleWatch();
    idleTimer = setInterval(() => {
      if (!running) return;
      if (lastChunkOpenLine && Date.now() - lastChunkAt > 250) showStdin();
    }, 120);
  };

  const stopIdleWatch = () => {
    if (idleTimer) {
      clearInterval(idleTimer);
      idleTimer = null;
    }
  };

  const start = async () => {
    if (running) return;
    source.close();
    pre.textContent = "";
    out.hidden = true;
    stderrBuf = "";
    errJump.hidden = true;
    lastChunkOpenLine = false;
    setRunning(true);
    setStatus("running", "运行中…");
    startIdleWatch();
    if (INPUT_HINT.test(area.value)) showStdin();

    let payload;
    try {
      payload = await postJSON("/api/run", {
        code: area.value,
        lesson_id: lessonId,
        allow_network: Boolean(options.allowNetwork),
        // 有 input() 的代码要留出打字时间，默认 5 秒是给纯计算块用的
        timeout: INPUT_HINT.test(area.value) ? 15 : undefined,
      });
    } catch (err) {
      setRunning(false);
      stopIdleWatch();
      out.hidden = false;
      setStatus("bad", "启动失败");
      append(String(err.message || err), "err");
      return;
    }

    source.open(payload.stream, {
      stdout: (data) => {
        append(data.text);
        lastChunkAt = Date.now();
        lastChunkOpenLine = !data.text.endsWith("\n");
      },
      stderr: (data) => {
        append(data.text, "err");
        stderrBuf += data.text;
        lastChunkAt = Date.now();
        lastChunkOpenLine = !data.text.endsWith("\n");
      },
      done: (data) => {
        finish(data);
        source.close();
      },
      error: () => {
        setStatus("bad", "连接中断");
        setRunning(false);
        stopIdleWatch();
      },
    });
  };

  runBtn.addEventListener("click", () => {
    if (running) {
      source.stop(source.runId);
      return;
    }
    start();
  });

  resetBtn.addEventListener("click", reset);
  errJump.addEventListener("click", () => selectLine(Number(errJump.dataset.line)));
  stdinBtn.addEventListener("click", sendLine);
  stdinInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendLine();
    }
  });

  area.addEventListener("input", syncGutter);
  area.addEventListener("scroll", () => {
    highlight.scrollTop = area.scrollTop;
    highlight.scrollLeft = area.scrollLeft;
  });

  const INDENT = "    ";
  const PAIRS = { "(": ")", "[": "]", "{": "}", '"': '"', "'": "'" };
  const CLOSERS = new Set([")", "]", "}", '"', "'"]);

  const applyIndent = (outdent) => {
    const { selectionStart: s, selectionEnd: e } = area;
    const v = area.value;
    const from = v.lastIndexOf("\n", s - 1) + 1;
    const nl = v.indexOf("\n", e);
    const to = nl === -1 ? v.length : nl;
    const chunk = v.slice(from, to);
    let removedAtStart = 0;
    const next = chunk
      .split("\n")
      .map((line, i) => {
        if (!outdent) return INDENT + line;
        const m = /^(\t| {1,4})/.exec(line);
        const cut = m ? m[1].length : 0;
        if (i === 0) removedAtStart = cut;
        return line.slice(cut);
      })
      .join("\n");
    area.value = v.slice(0, from) + next + v.slice(to);
    const firstShift = outdent ? -removedAtStart : INDENT.length;
    if (s === e) {
      area.selectionStart = area.selectionEnd = Math.max(from, s + firstShift);
    } else {
      area.selectionStart = s + firstShift;
      area.selectionEnd = e + (next.length - chunk.length);
    }
    syncGutter();
  };

  area.addEventListener("keydown", (event) => {
    const s = area.selectionStart;
    const e = area.selectionEnd;

    if (event.key === "Tab") {
      event.preventDefault();
      applyIndent(event.shiftKey);
      return;
    }

    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      start();
      return;
    }

    // 回车自动继承缩进；行尾是冒号时多缩一层
    if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey) {
      const before = area.value.slice(0, s);
      const line = before.slice(before.lastIndexOf("\n") + 1);
      const indent = /^[ \t]*/.exec(line)[0];
      const extra = line.trimEnd().endsWith(":") ? INDENT : "";
      if (indent || extra) {
        event.preventDefault();
        const insert = "\n" + indent + extra;
        area.value = area.value.slice(0, s) + insert + area.value.slice(e);
        area.selectionStart = area.selectionEnd = s + insert.length;
        syncGutter();
      }
      return;
    }

    // 括号/引号配对：选中内容时包起来，光标贴着右括号时跳过
    if (PAIRS[event.key] && !event.ctrlKey && !event.metaKey) {
      const close = PAIRS[event.key];
      if (s === e) {
        const nextChar = area.value[s] || "";
        if (nextChar === close) {
          event.preventDefault();
          area.selectionStart = area.selectionEnd = s + 1;
          return;
        }
        const isQuote = close === event.key;
        if (isQuote && nextChar && !/[\s)\]}:,.]/.test(nextChar)) return;
        event.preventDefault();
        area.value = area.value.slice(0, s) + event.key + close + area.value.slice(s);
        area.selectionStart = area.selectionEnd = s + 1;
        syncGutter();
        return;
      }
      if (!CLOSERS.has(close)) {
        event.preventDefault();
        const selected = area.value.slice(s, e);
        area.value = area.value.slice(0, s) + event.key + selected + close + area.value.slice(e);
        area.selectionStart = s + 1;
        area.selectionEnd = s + 1 + selected.length;
        syncGutter();
      }
    }
  });

  // 元素此时还没进 DOM，scrollHeight 为 0；等一帧再测量。
  requestAnimationFrame(syncGutter);

  return root;
}

/* 封装 EventSource：把 server 的命名事件分发给回调。 */
class EventSourceStream {
  constructor() {
    this.es = null;
    this.runId = null;
  }

  open(url, handlers) {
    this.close();
    this.runId = url.split("/").pop();
    const es = new EventSource(url);
    this.es = es;

    for (const name of ["stdout", "stderr", "done"]) {
      if (!handlers[name]) continue;
      es.addEventListener(name, (event) => {
        if (!event.data) return;
        try {
          handlers[name](JSON.parse(event.data));
        } catch {
          handlers[name]({ text: event.data });
        }
      });
    }
    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) {
        handlers.error?.();
      }
    };
  }

  async stop(runId) {
    if (!runId) return;
    try {
      await postJSON(`/api/run/${runId}/stop`, {});
    } catch {
      /* 进程可能已经结束，忽略 */
    }
  }

  close() {
    if (this.es) {
      this.es.close();
      this.es = null;
    }
  }
}
