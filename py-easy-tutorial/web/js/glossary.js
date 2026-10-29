/* 交互式术语表：客户端过滤，词条可跳回对应课程。 */

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function createGlossary(block, lessonId, options = {}) {
  const root = el("div", "glossary");

  const search = el("input", "gl-search");
  search.type = "search";
  search.placeholder = `在 ${block.terms.length} 个术语中筛选…`;
  search.setAttribute("aria-label", "筛选术语");
  root.append(search);

  const list = el("div", "gl-list");
  root.append(list);

  const lessonByOrder = new Map();
  for (const lesson of options.lessons || []) {
    lessonByOrder.set(lesson.order, lesson);
  }

  const render = (query) => {
    const q = query.trim().toLowerCase();
    list.innerHTML = "";
    let shown = 0;

    for (const entry of block.terms) {
      const text = entry.term + " " + entry.definition;
      if (q && !text.toLowerCase().includes(q)) continue;
      shown += 1;

      const row = el("div", "gl-row");
      const term = el("div", "gl-term");
      term.innerHTML = entry.term;
      row.append(term);

      const def = el("div", "gl-def");
      def.innerHTML = entry.definition;
      row.append(def);

      if (entry.order && lessonByOrder.get(entry.order)) {
        const target = lessonByOrder.get(entry.order);
        const link = el("a", "gl-link", `→ 第 ${entry.order} 课`);
        link.href = `#/lesson/${target.id}`;
        row.append(link);
      }
      list.append(row);
    }

    if (!shown) {
      list.append(el("div", "gl-empty", "没有匹配的术语"));
    }
  };

  search.addEventListener("input", () => render(search.value));
  render("");

  return root;
}
