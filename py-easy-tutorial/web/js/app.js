/* 应用入口：路由、目录、首页、课程页、页内目录。无框架，无构建。 */

import { getJSON } from "./api.js";
import {
  exportProgress,
  importProgress,
  isLessonDone,
  loadProgress,
  markLessonDone,
  progress,
} from "./progress.js";
import { renderBlocks } from "./renderer.js";

const GROUP_LABELS = {
  beginner: "Beginner",
  moderate: "Moderate",
  advanced: "Advanced",
  general: "General",
  resources: "Python 3.x Resources",
};

const state = {
  index: null,
  byId: new Map(),
  lessonId: null,
  disposeSpy: null,
};

const $ = (id) => document.getElementById(id);

/* 关掉浏览器的滚动位置恢复：刷新带锚点的链接时，浏览器会把我们刚滚到的小节
   又拉回顶部，和路由自己的定位打架。 */
if ("scrollRestoration" in history) history.scrollRestoration = "manual";

/* ---------------- 主题 ---------------- */

function applyTheme() {
  const saved = localStorage.getItem("pytut-theme") || "dark";
  document.documentElement.dataset.theme = saved;
}

$("theme-btn").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("pytut-theme", next);
});

/* ---------------- 目录 ---------------- */

function renderNav() {
  const nav = $("nav");
  nav.innerHTML = "";

  for (const stage of state.index.stages) {
    const block = document.createElement("div");
    block.className = "nav-stage";

    const head = document.createElement("div");
    head.className = "nav-stage-head";
    head.innerHTML = `<b>${stage.title}</b><span>${stage.lessons.length}</span>`;
    block.append(head);

    if (!stage.lessons.length) {
      const empty = document.createElement("div");
      empty.className = "nav-empty";
      empty.textContent = "内容编写中";
      block.append(empty);
    }

    for (const lesson of stage.lessons) {
      const link = document.createElement("a");
      link.className = "nav-item";
      link.href = `#/lesson/${lesson.id}`;
      link.dataset.id = lesson.id;
      link.innerHTML = `<span class="num">${lesson.order}</span><span>${lesson.title}</span>`;
      if (isLessonDone(lesson.id)) {
        link.classList.add("done");
        const tick = document.createElement("span");
        tick.className = "tick";
        tick.textContent = "✓";
        link.append(tick);
      }
      block.append(link);
    }

    nav.append(block);
  }

  updateFoot();
}

function updateFoot() {
  const data = progress();
  const done = Object.values(data.lessons || {}).filter((x) => x.status === "done").length;
  $("progress-text").textContent = `${state.index.published} / ${state.index.planned_total} 课已上线`;
  $("xp-text").textContent = `完成 ${done} 课 · ${data.xp || 0} XP · 连续 ${data.streak?.current || 0} 天`;
  $("brand-sub").textContent = `Python ${state.index.python} · 本地执行`;
}

function refreshNavDone(lessonId) {
  const link = document.querySelector(`.nav-item[data-id="${lessonId}"]`);
  if (!link || link.classList.contains("done")) return;
  link.classList.add("done");
  const tick = document.createElement("span");
  tick.className = "tick";
  tick.textContent = "✓";
  link.append(tick);
}

function highlightNav(id) {
  document.querySelectorAll(".nav-item").forEach((node) => {
    node.classList.toggle("active", node.dataset.id === id);
  });
}

/* ---------------- 首页 ---------------- */

function renderHome() {
  state.lessonId = null;
  state.disposeSpy?.();
  state.disposeSpy = null;
  $("toc-rail").innerHTML = "";
  document.title = "交互式 Python 教程";
  highlightNav(null);

  const view = $("view");
  view.innerHTML = "";

  const hero = document.createElement("section");
  hero.className = "hero";

  const published = state.index.published;
  const total = state.index.planned_total;

  hero.innerHTML = `
    <div class="kicker">Python ${state.index.python} · 真实解释器执行</div>
    <h1>把每段代码都真的跑一遍</h1>
    <p>103 课按难度分成六个阶段，从「能跑」到「能读 CPython 源码」。每段示例都在本地子进程里真实执行，
       不是静态截图；每道题都有隐藏测试，答错会逐级给提示。</p>
    <p>没有账号，没有联网请求，进度只存在这台机器上。</p>
    <div class="stats">
      <div class="stat"><b>${published}</b><span>已上线课程</span></div>
      <div class="stat"><b>${total}</b><span>规划总课数</span></div>
      <div class="stat"><b>${state.index.stages.length}</b><span>难度阶段</span></div>
    </div>
  `;

  const last = localStorage.getItem("pytut-last");
  if (last && state.byId.get(last)) {
    const target = state.byId.get(last);
    const resume = document.createElement("a");
    resume.className = "resume-card";
    resume.href = `#/lesson/${last}`;
    resume.innerHTML = `<span class="rc-label">继续上次</span><strong>${target.order}. ${target.title}</strong>`;
    hero.append(resume);
  }

  const weakEntries = Object.entries(progress().weak || {})
    .filter(([key, count]) => key.startsWith("lesson:") && count > 0)
    .map(([key]) => key.slice(7))
    .filter((id) => state.byId.get(id));
  if (weakEntries.length) {
    const review = document.createElement("div");
    review.className = "review-box";
    const label = document.createElement("div");
    label.className = "review-label";
    label.textContent = "需要复习（练习未通过）";
    review.append(label);
    const links = document.createElement("div");
    links.className = "review-links";
    for (const id of weakEntries.slice(0, 6)) {
      const target = state.byId.get(id);
      const link = document.createElement("a");
      link.href = `#/lesson/${id}`;
      link.textContent = `${target.order}. ${target.title}`;
      links.append(link);
    }
    review.append(links);
    hero.append(review);
  }

  const grid = document.createElement("div");
  grid.className = "stage-grid";

  for (const stage of state.index.stages) {
    const count = stage.lessons.length;
    const card = document.createElement(count ? "a" : "div");
    card.className = "stage-card";
    if (count) {
      card.href = `#/lesson/${stage.lessons[0].id}`;
    } else {
      card.style.opacity = "0.5";
      card.style.cursor = "default";
    }
    card.innerHTML = `
      <div class="sc-top">
        <span class="sc-id">${stage.id.toUpperCase()}</span>
        <span class="sc-count">${count} 课</span>
      </div>
      <h3>${stage.title}</h3>
      <p>${stage.subtitle}${count ? "" : " · 即将上线"}</p>
    `;
    grid.append(card);
  }

  hero.append(grid);
  view.append(hero);
}

/* ---------------- 页内目录 ---------------- */

function tocLinks(lesson, heads) {
  const list = document.createElement("ol");
  list.className = "toc-list";

  for (const head of heads) {
    const li = document.createElement("li");
    li.className = head.tagName === "H3" ? "lv3" : "lv2";
    const link = document.createElement("a");
    link.href = `#/lesson/${lesson.id}/${head.id}`;
    link.dataset.target = head.id;
    link.textContent = head.textContent.trim();
    li.append(link);
    list.append(li);
  }
  return list;
}

function buildToc(article, lesson) {
  const heads = [...article.querySelectorAll("h2[id], h3[id]")];
  const rail = $("toc-rail");
  rail.innerHTML = "";

  if (heads.length < 2) return;

  // 正文顶部的折叠目录：窄屏（含预览面板）时唯一的跳转入口
  const details = document.createElement("details");
  details.className = "toc-inline";
  details.open = heads.length <= 10;
  const summary = document.createElement("summary");
  summary.textContent = `本页目录 · ${heads.length} 节`;
  details.append(summary, tocLinks(lesson, heads));
  const headNode = article.querySelector(".lesson-head");
  if (headNode) headNode.after(details);
  else article.prepend(details);

  // 宽屏右侧常驻目录
  const title = document.createElement("div");
  title.className = "toc-title";
  title.textContent = "本页目录";
  rail.append(title, tocLinks(lesson, heads));

  // 滚动高亮：只更新样式，不做额外布局读取之外的 DOM 操作
  const links = [...rail.querySelectorAll("a")];
  const update = () => {
    let current = heads[0].id;
    for (const head of heads) {
      if (head.getBoundingClientRect().top <= 120) current = head.id;
      else break;
    }
    for (const link of links) {
      link.classList.toggle("active", link.dataset.target === current);
    }
  };

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      update();
      ticking = false;
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  update();
  state.disposeSpy = () => window.removeEventListener("scroll", onScroll);
}

function scrollToAnchor(anchor, smooth = true) {
  if (!anchor) return;
  const target = document.getElementById(anchor);
  if (!target) return;
  // 不用 requestAnimationFrame：后台标签页里 rAF 会被挂起，锚点就永远不生效。
  // 元素已经插进 DOM，scrollIntoView 自己会触发一次布局。
  target.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
}

/* ---------------- 课程页 ---------------- */

async function loadLesson(id) {
  const view = $("view");
  view.innerHTML = '<div class="loading">正在载入…</div>';

  let lesson;
  try {
    lesson = await getJSON(`/api/lessons/${id}`);
  } catch (err) {
    view.innerHTML = `<div class="fatal"><h2>读不到这门课</h2><p>${err.message}</p></div>`;
    return false;
  }

  state.lessonId = id;
  localStorage.setItem("pytut-last", id);
  state.disposeSpy?.();
  state.disposeSpy = null;

  document.title = `${lesson.title} · 交互式 Python 教程`;
  highlightNav(id);
  closeDrawer();

  view.innerHTML = "";
  const article = document.createElement("article");
  article.className = "prose";

  const crumb = document.createElement("div");
  crumb.className = "crumb";
  crumb.innerHTML = `<a href="#/">全部课程</a> · ${lesson.stage.toUpperCase()} ${lesson.stage_title} · 第 ${lesson.order} 课`;
  article.append(crumb);

  const head = document.createElement("header");
  head.className = "lesson-head";
  const h1 = document.createElement("h1");
  h1.textContent = lesson.title;
  const chips = document.createElement("div");
  chips.className = "chips";
  const group = document.createElement("span");
  group.className = "chip group";
  group.textContent = GROUP_LABELS[lesson.official_group] || lesson.official_group;
  chips.append(group);
  for (const concept of lesson.concepts) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = concept;
    chips.append(chip);
  }
  head.append(h1, chips);
  article.append(head);

  article.append(
    renderBlocks(lesson.blocks, lesson.id, {
      allowNetwork: lesson.allow_network,
      lessons: state.index.lessons,
    }),
  );

  if (lesson.doc_refs?.length) {
    const refs = document.createElement("div");
    refs.className = "docrefs";
    const title = document.createElement("h4");
    title.textContent = "对应官方文档";
    refs.append(title);
    for (const ref of lesson.doc_refs) {
      const link = document.createElement("a");
      link.href = ref.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = `↗ ${ref.title}`;
      refs.append(link);
    }
    article.append(refs);
  }

  article.append(buildDoneBar(lesson));
  article.append(buildPager(lesson));
  view.append(article);

  buildToc(article, lesson);
  window.scrollTo(0, 0);
  return true;
}

function buildDoneBar(lesson) {
  const bar = document.createElement("div");
  bar.className = "lesson-done";

  const btn = document.createElement("button");
  btn.className = "cb-btn primary";
  const hint = document.createElement("span");
  hint.className = "lesson-done-hint";
  hint.textContent = "记录到进度，可导出备份。";

  const sync = () => {
    const done = isLessonDone(lesson.id);
    btn.textContent = done ? "本课已完成 ✓" : "标记本课完成  +20 XP";
    btn.disabled = done;
    bar.classList.toggle("is-done", done);
  };

  btn.addEventListener("click", () => {
    if (!markLessonDone(lesson.id)) return;
    sync();
    refreshNavDone(lesson.id);
    updateFoot();
  });

  sync();
  bar.append(btn, hint);
  return bar;
}

function buildPager(lesson) {
  const pager = document.createElement("nav");
  pager.className = "pager";

  const prev = lesson.prev ? state.byId.get(lesson.prev) : null;
  const next = lesson.next ? state.byId.get(lesson.next) : null;

  if (prev) {
    const a = document.createElement("a");
    a.href = `#/lesson/${prev.id}`;
    a.innerHTML = `<small>上一课</small>${prev.order}. ${prev.title}`;
    pager.append(a);
  }
  if (next) {
    const a = document.createElement("a");
    a.className = "next";
    a.href = `#/lesson/${next.id}`;
    a.innerHTML = `<small>下一课</small>${next.order}. ${next.title}`;
    pager.append(a);
  }
  return pager;
}

/* ---------------- 路由 ---------------- */

async function route() {
  const hash = location.hash || "#/";
  const match = hash.match(/^#\/lesson\/([\w-]+)(?:\/([\w-]+))?$/);

  if (!match) {
    renderHome();
    return;
  }

  const [, id, anchor] = match;
  if (state.lessonId === id) {
    if (anchor) scrollToAnchor(anchor);
    else window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  const ok = await loadLesson(id);
  if (ok && anchor) scrollToAnchor(anchor, false);
}

/* ---------------- 移动端抽屉 ---------------- */

function closeDrawer() {
  $("sidebar").classList.remove("open");
}

$("drawer-btn").addEventListener("click", () => {
  $("sidebar").classList.toggle("open");
});

document.addEventListener("click", (event) => {
  const sidebar = $("sidebar");
  if (
    sidebar.classList.contains("open") &&
    !sidebar.contains(event.target) &&
    event.target.id !== "drawer-btn"
  ) {
    sidebar.classList.remove("open");
  }
});

/* ---------------- 搜索与快捷键 ---------------- */

const search = { entries: [], items: [], active: 0 };

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };
const escapeHtml = (text) => String(text).replace(/[&<>]/g, (ch) => ESCAPES[ch]);

function markMatch(text, query) {
  const q = query.trim().toLowerCase();
  if (!q) return escapeHtml(text);
  const idx = text.toLowerCase().indexOf(q);
  if (idx === -1) return escapeHtml(text);
  return (
    escapeHtml(text.slice(0, idx)) +
    "<mark>" + escapeHtml(text.slice(idx, idx + q.length)) + "</mark>" +
    escapeHtml(text.slice(idx + q.length))
  );
}

function buildSearchIndex() {
  const entries = [];
  for (const lesson of state.index.lessons) {
    const stage = state.index.stages.find((s) => s.id === lesson.stage);
    const stageTitle = stage ? stage.title : "";
    entries.push({
      lessonId: lesson.id,
      order: lesson.order,
      title: lesson.title,
      stage: stageTitle,
      sub: "",
      anchor: null,
      kind: "lesson",
      haystack: `${lesson.title} ${lesson.concepts.join(" ")}`.toLowerCase(),
    });
    for (const section of lesson.outline || []) {
      entries.push({
        lessonId: lesson.id,
        order: lesson.order,
        title: lesson.title,
        stage: stageTitle,
        sub: section.text,
        anchor: section.anchor,
        kind: "section",
        haystack: `${section.text} ${lesson.title}`.toLowerCase(),
      });
    }
  }
  search.entries = entries;
}

function searchEntries(query) {
  const q = query.trim().toLowerCase();
  if (!q) {
    return search.entries.filter((e) => e.kind === "lesson").slice(0, 10);
  }
  const hits = [];
  for (const entry of search.entries) {
    const idx = entry.haystack.indexOf(q);
    if (idx === -1) continue;
    const titleIdx = entry.title.toLowerCase().indexOf(q);
    let score = idx;
    if (titleIdx === 0) score -= 1000;
    else if (titleIdx > 0) score -= 500;
    if (entry.kind === "lesson") score -= 120;
    hits.push({ entry, score });
  }
  hits.sort((a, b) => a.score - b.score || a.entry.order - b.entry.order);
  return hits.slice(0, 12).map((h) => h.entry);
}

function renderSearch(query) {
  const items = searchEntries(query);
  search.items = items;
  if (search.active >= items.length) search.active = 0;

  const box = $("palette-results");
  box.innerHTML = "";
  if (!items.length) {
    box.innerHTML = '<div class="palette-empty">没有匹配的课程或小节</div>';
    return;
  }

  items.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "palette-item" + (index === search.active ? " active" : "");
    row.innerHTML = `
      <span class="pi-order">${item.order}</span>
      <span class="pi-main">
        <span class="pi-title">${markMatch(item.title, query)}</span>
        <span class="pi-sub">${escapeHtml(item.stage)}${item.sub ? " › " + markMatch(item.sub, query) : ""}</span>
      </span>`;
    row.addEventListener("click", () => openEntry(item));
    box.append(row);
  });
}

function moveSearch(delta) {
  const total = search.items.length;
  if (!total) return;
  search.active = (search.active + delta + total) % total;
  const box = $("palette-results");
  [...box.children].forEach((node, i) => {
    node.classList.toggle("active", i === search.active);
  });
  box.children[search.active]?.scrollIntoView({ block: "nearest" });
}

function openEntry(item) {
  closePalette();
  const hash = item.anchor
    ? `#/lesson/${item.lessonId}/${item.anchor}`
    : `#/lesson/${item.lessonId}`;
  if (location.hash === hash) route();
  else location.hash = hash;
}

function openPalette() {
  $("shortcuts").hidden = true;
  $("palette").hidden = false;
  const input = $("palette-input");
  input.value = "";
  search.active = 0;
  renderSearch("");
  input.focus();
}

function closePalette() {
  $("palette").hidden = true;
}

$("palette-input").addEventListener("input", (event) => {
  search.active = 0;
  renderSearch(event.target.value);
});

$("palette-input").addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    moveSearch(1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    moveSearch(-1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    const item = search.items[search.active];
    if (item) openEntry(item);
  } else if (event.key === "Escape") {
    event.preventDefault();
    closePalette();
  }
});

$("palette").addEventListener("click", (event) => {
  if (event.target.id === "palette") closePalette();
});

$("shortcuts").addEventListener("click", (event) => {
  if (event.target.id === "shortcuts") $("shortcuts").hidden = true;
});

function gotoRelative(delta) {
  const list = state.index.lessons;
  if (!list.length || !state.lessonId) return;
  const index = list.findIndex((item) => item.id === state.lessonId);
  if (index === -1) return;
  const target = list[index + delta];
  if (target) location.hash = `#/lesson/${target.id}`;
}

document.addEventListener("keydown", (event) => {
  const tag = (event.target.tagName || "").toLowerCase();
  const typing = tag === "input" || tag === "textarea" || event.target.isContentEditable;

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    if ($("palette").hidden) openPalette();
    else closePalette();
    return;
  }

  if (event.key === "Escape") {
    closePalette();
    $("shortcuts").hidden = true;
    $("sidebar").classList.remove("open");
    return;
  }

  if (typing) return;

  if (event.key === "?") {
    event.preventDefault();
    const panel = $("shortcuts");
    panel.hidden = !panel.hidden;
    return;
  }

  if (event.altKey && event.key === "ArrowLeft") {
    event.preventDefault();
    gotoRelative(-1);
  } else if (event.altKey && event.key === "ArrowRight") {
    event.preventDefault();
    gotoRelative(1);
  }
});

/* ---------------- 进度导入导出 ---------------- */

$("export-btn").addEventListener("click", exportProgress);

$("import-btn").addEventListener("click", () => $("import-file").click());

$("import-file").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    await importProgress(file);
    renderNav();
    route();
  } catch (err) {
    alert(`导入失败：${err.message}`);
  } finally {
    event.target.value = "";
  }
});

/* ---------------- 启动 ---------------- */

async function boot() {
  applyTheme();
  try {
    state.index = await getJSON("/api/lessons");
  } catch (err) {
    $("view").innerHTML = `
      <div class="fatal">
        <h2>还没有课程数据</h2>
        <p>${err.message}</p>
        <code>python build.py</code>
      </div>`;
    $("progress-text").textContent = "未编译";
    return;
  }
  for (const item of state.index.lessons) state.byId.set(item.id, item);
  buildSearchIndex();
  await loadProgress();
  renderNav();
  window.addEventListener("hashchange", route);
  route();
}

boot();
