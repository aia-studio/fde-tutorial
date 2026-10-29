/* 块数组 → DOM。渲染器只认 AST，不解析 Markdown——解析全部发生在构建期。 */

import { createCodeBlock } from "./codeblock.js";
import { createExercise } from "./exercise.js";
import { createGlossary } from "./glossary.js";
import { createQuiz } from "./quiz.js";
import { createStepper } from "./stepper.js";

const HEADING_TAGS = { 1: "h2", 2: "h2", 3: "h3", 4: "h4", 5: "h4", 6: "h4" };

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* 标题锚点用序号而不是 slug：中文标题转成 slug 会得到一长串百分号编码，
   而 `sec-3` 短、稳定、可以直接贴进对话里。 */
export function renderBlocks(blocks, lessonId, options = {}) {
  const frag = document.createDocumentFragment();
  let quizIndex = 0;
  let stepIndex = 0;
  let headingIndex = 0;

  for (const block of blocks) {
    switch (block.type) {
      case "heading": {
        const h = el(HEADING_TAGS[block.level] || "h3");
        h.innerHTML = block.html;
        if (block.level <= 3) {
          headingIndex += 1;
          h.id = `sec-${headingIndex}`;
        }
        frag.append(h);
        break;
      }
      case "p": {
        const p = el("p");
        p.innerHTML = block.html;
        frag.append(p);
        break;
      }
      case "list": {
        const list = el(block.ordered ? "ol" : "ul");
        for (const item of block.items) {
          const li = el("li");
          li.innerHTML = item;
          list.append(li);
        }
        frag.append(list);
        break;
      }
      case "table": {
        const table = el("table");
        const thead = el("thead");
        const tr = el("tr");
        for (const cell of block.head) {
          const th = el("th");
          th.innerHTML = cell;
          tr.append(th);
        }
        thead.append(tr);
        const tbody = el("tbody");
        for (const row of block.rows) {
          const r = el("tr");
          for (const cell of row) {
            const td = el("td");
            td.innerHTML = cell;
            r.append(td);
          }
          tbody.append(r);
        }
        table.append(thead, tbody);
        frag.append(table);
        break;
      }
      case "callout": {
        const box = el("div", `callout ${block.kind || "note"}`);
        if (block.kind !== "quote") {
          const title = el("div", "callout-title");
          title.innerHTML = block.title || defaultTitle(block.kind);
          box.append(title);
        }
        const body = el("div", "callout-body");
        body.innerHTML = block.html;
        box.append(body);
        frag.append(box);
        break;
      }
      case "code": {
        frag.append(createCodeBlock(block, lessonId, options));
        if (block.expect) {
          const wrap = el("div", "expected");
          const label = el("span", "lbl", "预期输出");
          const pre = el("pre");
          pre.textContent = block.expect;
          wrap.append(label, pre);
          frag.append(wrap);
        }
        break;
      }
      case "output": {
        const wrap = el("div", "expected");
        const pre = el("pre");
        pre.textContent = block.text;
        wrap.append(pre);
        frag.append(wrap);
        break;
      }
      case "quiz": {
        quizIndex += 1;
        frag.append(createQuiz(block, `${lessonId}:${quizIndex}`));
        break;
      }
      case "exercise": {
        frag.append(createExercise(block, lessonId));
        break;
      }
      case "step": {
        stepIndex += 1;
        frag.append(createStepper(block, stepIndex));
        break;
      }
      case "glossary": {
        frag.append(createGlossary(block, lessonId, options));
        break;
      }
      case "hr":
        frag.append(el("hr"));
        break;
      default:
        break;
    }
  }

  return frag;
}

function defaultTitle(kind) {
  return (
    {
      note: "说明",
      tip: "技巧",
      warn: "注意",
      danger: "警告",
      why: "为什么",
    }[kind] || "提示"
  );
}
