/* 进度：客户端持有状态，变更后防抖 PUT 给服务端落盘。
 *
 * 为什么不在服务端算：XP、连续天数都依赖"本地今天"，服务端和浏览器在同一台机器上，
 * 但用户可能在 23:59 打开页面、00:01 提交，客户端算更贴近直觉。
 */

import { getJSON, putJSON } from "./api.js";

const state = {
  data: null,
  timer: null,
  pending: false,
};

function defaults() {
  return {
    schema: 1,
    xp: 0,
    streak: { current: 0, best: 0, last_day: null },
    lessons: {},
    exercises: {},
    quizzes: {},
    weak: {},
  };
}

const pad = (n) => String(n).padStart(2, "0");

export function todayString() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function dayGap(from, to) {
  const a = new Date(`${from}T00:00:00`);
  const b = new Date(`${to}T00:00:00`);
  return Math.round((b - a) / 86400000);
}

export async function loadProgress() {
  try {
    const data = await getJSON("/api/progress");
    state.data = { ...defaults(), ...data };
    state.data.streak = { ...defaults().streak, ...(data.streak || {}) };
  } catch {
    state.data = defaults();
  }
  return state.data;
}

export function progress() {
  return state.data || defaults();
}

/* ---------- 写入 ---------- */

export function queueSave() {
  state.pending = true;
  clearTimeout(state.timer);
  state.timer = setTimeout(() => flushSave(), 400);
}

export async function flushSave() {
  if (!state.pending) return;
  state.pending = false;
  try {
    const saved = await fetch("/api/progress", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(progress()),
    });
    if (saved.ok) {
      const data = await saved.json();
      state.data.updated_at = data.updated_at;
    }
  } catch {
    state.pending = true;
  }
}

/* ---------- 计数 ---------- */

export function touchStreak() {
  const data = progress();
  const today = todayString();
  const streak = data.streak;
  if (streak.last_day === today) return;

  if (streak.last_day && dayGap(streak.last_day, today) <= 2) {
    // 隔一天也算连着：允许一次"宽限"，但不额外加天数
    streak.current = (streak.current || 0) + 1;
  } else {
    streak.current = 1;
  }
  streak.last_day = today;
  streak.best = Math.max(streak.best || 0, streak.current);
  queueSave();
}

export function addXp(amount) {
  if (!amount) return;
  const data = progress();
  data.xp = (data.xp || 0) + amount;
  touchStreak();
  queueSave();
}

export function isLessonDone(lessonId) {
  return Boolean(progress().lessons?.[lessonId]?.status === "done");
}

export function markLessonDone(lessonId) {
  const data = progress();
  if (isLessonDone(lessonId)) return false;
  data.lessons[lessonId] = {
    status: "done",
    at: new Date().toISOString(),
  };
  addXp(20);
  return true;
}

export function exerciseState(exerciseId) {
  return progress().exercises?.[exerciseId] || null;
}

export function recordExercise(exerciseId, passed, lessonId) {
  const data = progress();
  const prev = data.exercises[exerciseId] || { attempts: 0, passed: false };

  data.exercises[exerciseId] = {
    attempts: (prev.attempts || 0) + 1,
    passed: Boolean(prev.passed || passed),
    at: new Date().toISOString(),
  };

  if (passed) {
    delete data.weak[exerciseId];
    if (lessonId) delete data.weak["lesson:" + lessonId];
  } else {
    data.weak[exerciseId] = (data.weak[exerciseId] || 0) + 1;
    if (lessonId) data.weak["lesson:" + lessonId] = (data.weak["lesson:" + lessonId] || 0) + 1;
  }

  queueSave();
  return data.exercises[exerciseId];
}

export function recordQuiz(key, correct) {
  const data = progress();
  const prev = data.quizzes[key] || { attempts: 0, correct: false };
  data.quizzes[key] = {
    attempts: (prev.attempts || 0) + 1,
    correct: Boolean(prev.correct || correct),
  };
  queueSave();
}

/* ---------- 导入导出 ---------- */

export function exportProgress() {
  const blob = new Blob([JSON.stringify(progress(), null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `pytut-progress-${todayString()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export async function importProgress(file) {
  const text = await file.text();
  const parsed = JSON.parse(text);
  const saved = await putJSON("/api/progress", parsed);
  state.data = { ...defaults(), ...saved };
  state.data.streak = { ...defaults().streak, ...(saved.streak || {}) };
  return state.data;
}
