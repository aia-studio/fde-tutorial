/* 测验块：点击即判，答错也给解释，记录到进度。 */

import { recordQuiz } from "./progress.js";

const STORE = "pytut-quiz:";

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function createQuiz(block, key) {
  const root = el("div", "quiz");

  const q = el("div", "quiz-q");
  q.innerHTML = block.question;
  root.append(q);

  const opts = el("div", "quiz-opts");
  const explain = el("div", "quiz-explain");
  explain.hidden = true;
  if (block.explain) explain.innerHTML = block.explain;

  const saved = localStorage.getItem(STORE + key);
  const buttons = [];

  const reveal = (chosen) => {
    buttons.forEach((btn, i) => {
      btn.disabled = true;
      if (i === block.answer) btn.classList.add("correct");
      else if (i === chosen) btn.classList.add("wrong");
    });
    explain.hidden = false;
  };

  block.options.forEach((text, i) => {
    const btn = el("button", "quiz-opt");
    btn.innerHTML = text;
    btn.type = "button";
    btn.addEventListener("click", () => {
      localStorage.setItem(STORE + key, String(i));
      recordQuiz(key, i === block.answer);
      reveal(i);
    });
    buttons.push(btn);
    opts.append(btn);
  });

  root.append(opts, explain);

  if (saved !== null) reveal(Number(saved));

  return root;
}
