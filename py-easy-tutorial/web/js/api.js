/* 极薄的 API 封装：把 HTTP 错误转成可读的中文消息，界面上不出现裸异常。 */

export async function getJSON(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).error || "";
    } catch {
      /* 忽略非 JSON 响应 */
    }
    throw new Error(detail || `请求失败（HTTP ${res.status}）`);
  }
  return res.json();
}

export async function postJSON(url, body) {
  return sendJSON("POST", url, body);
}

export async function putJSON(url, body) {
  return sendJSON("PUT", url, body);
}

async function sendJSON(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).error || "";
    } catch {
      /* 忽略非 JSON 响应 */
    }
    throw new Error(detail || `请求失败（HTTP ${res.status}）`);
  }
  return res.json();
}
