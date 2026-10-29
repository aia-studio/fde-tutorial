/* 练习块：编辑代码 → 服务端跑隐藏测试 → 逐条结果 + 提示阶梯。 */

import { postJSON } from "./api.js";
import { highlightPython } from "./highlight.js";
import { addXp, exerciseState, recordExercise } from "./progress.js";

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function createExercise(block, lessonId) {
  const root = el("section", "exercise");
  root.id = `ex-${block.id}`;

  const head = el("div", "ex-head");
  head.append(
    el("span", "ex-tag", "练习"),
    el("span", "ex-title", "")
  );
  head.querySelector(".ex-title").innerHTML = block.title;
  head.append(el("span", "ex-xp", `+${block.xp} XP`));
  root.append(head);

  const prompt = el("div", "ex-prompt");
  prompt.innerHTML = block.prompt;
  root.append(prompt);

  const wrap = el("div", "ex-editor");
  const highlight = el("pre", "ex-highlight");
  highlight.setAttribute("aria-hidden", "true");
  const area = el("textarea", "ex-code");
  area.value = block.starter || "";
  area.spellcheck = false;
  area.setAttribute("aria-label", "练习代码");
  wrap.append(highlight, area);
  root.append(wrap);

  const actions = el("div", "ex-actions");
  const submit = el("button", "cb-btn primary", "提交");
  const reset = el("button", "cb-btn", "重置");
  const status = el("span", "ex-status", "待提交");
  actions.append(submit, reset, status);
  root.append(actions);

  const results = el("div", "ex-results");
  root.append(results);

  const hints = el("div", "ex-hints");
  root.append(hints);

  const solutionBox = el("div", "ex-solution");
  solutionBox.hidden = true;
  root.append(solutionBox);

  const success = el("div", "ex-success", "全部通过");
  success.hidden = true;
  root.append(success);

  let failures = 0;
  let busy = false;
  let passed = Boolean(exerciseState(block.id)?.passed);

  const syncHighlight = () => {
    highlight.innerHTML = highlightPython(area.value) + "\n";
    area.style.height = "auto";
    area.style.height = Math.max(area.scrollHeight, 76) + "px";
    highlight.style.minHeight = area.scrollHeight + "px";
  };

  const renderHints = () => {
    hints.innerHTML = "";
    if (!failures || !block.hints?.length) return;
    const show = Math.min(failures, block.hints.length);
    const title = el("div", "ex-hints-title", `提示（${show}/${block.hints.length}）`);
    hints.append(title);
    for (let i = 0; i < show; i += 1) {
      const item = el("div", "ex-hint");
      item.innerHTML = block.hints[i];
      hints.append(item);
    }
  };

  const markPassed = (fresh) => {
    passed = true;
    success.hidden = false;
    submit.disabled = true;
    area.readOnly = true;
    status.textContent = "已通过";
    if (fresh) {
      addXp(block.xp);
      success.textContent = `全部通过，+${block.xp} XP`;
    } else {
      success.textContent = "这道题之前已经通过";
    }
  };

  const renderResults = (data) => {
    results.innerHTML = "";
    if (data.timed_out) {
      results.append(el("div", "ex-row bad", "执行超时（超过 10 秒），检查是否有死循环"));
      return;
    }
    if (!data.results?.length) {
      const row = el("div", "ex-row bad", "没能跑起来：");
      row.append(el("code", "", (data.stderr || "").split("\n").slice(-3).join("\n")));
      results.append(row);
      return;
    }
    for (const item of data.results) {
      const row = el("div", "ex-row " + (item.passed ? "ok" : "bad"));
      row.append(el("span", "ex-mark", item.passed ? "✓" : "✗"));
      row.append(el("span", "ex-name", item.name));
      if (!item.passed && item.error) {
        row.append(el("div", "ex-error", item.error));
      }
      results.append(row);
    }
  };

  const check = async () => {
    if (busy || passed) return;
    busy = true;
    submit.disabled = true;
    status.textContent = "判题中…";

    let data;
    try {
      data = await postJSON("/api/check", {
        lesson_id: lessonId,
        exercise_id: block.id,
        code: area.value,
      });
    } catch (err) {
      status.textContent = "提交失败";
      results.innerHTML = "";
      results.append(el("div", "ex-row bad", String(err.message || err)));
      submit.disabled = false;
      busy = false;
      return;
    }

    renderResults(data);
    const alreadyPassed = Boolean(exerciseState(block.id)?.passed);
    recordExercise(block.id, data.passed, lessonId);

    if (data.passed) {
      markPassed(!alreadyPassed);
    } else {
      failures += 1;
      status.textContent = data.timed_out ? "超时" : `未通过 · 第 ${failures} 次`;
      submit.disabled = false;
      renderHints();
      if (failures >= 3 && block.solution) {
        showSolution();
      }
    }
    busy = false;
  };

  const showSolution = () => {
    if (!solutionBox.hidden) return;
    solutionBox.hidden = false;
    solutionBox.innerHTML = "";
    const note = el("div", "ex-solution-note", "连续 3 次未通过，可以对照参考实现——先自己找一遍差异再粘。");
    const pre = el("pre", "ex-solution-code");
    pre.textContent = block.solution;
    solutionBox.append(note, pre);
  };

  submit.addEventListener("click", check);
  reset.addEventListener("click", () => {
    if (passed) return;
    area.value = block.starter || "";
    syncHighlight();
    results.innerHTML = "";
    hints.innerHTML = "";
    failures = 0;
    status.textContent = "待提交";
  });

  area.addEventListener("input", syncHighlight);
  area.addEventListener("keydown", (event) => {
    if (event.key === "Tab") {
      event.preventDefault();
      const { selectionStart: s, selectionEnd: e } = area;
      area.value = area.value.slice(0, s) + "    " + area.value.slice(e);
      area.selectionStart = area.selectionEnd = s + 4;
      syncHighlight();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      check();
    }
  });

  requestAnimationFrame(syncHighlight);

  if (passed) {
    markPassed(false);
  }

  return root;
}
