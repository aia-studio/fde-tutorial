/* Python 词法着色。只做单遍扫描，不建 AST —— 编辑器要的是"看起来对"，不是语义分析。 */

const KEYWORDS = new Set(
  ("False None True and as assert async await break class continue def del elif else "
    + "except finally for from global if import in is lambda match case nonlocal not or "
    + "pass raise return try while with yield").split(" ")
);

const BUILTINS = new Set(
  ("abs aiter all anext any ascii bin bool breakpoint bytearray bytes callable chr "
    + "classmethod compile complex delattr dict dir divmod enumerate eval exec filter "
    + "float format frozenset getattr globals hasattr hash help hex id input int isinstance "
    + "issubclass iter len list locals map max memoryview min next object oct open ord pow "
    + "print property range repr reversed round set setattr slice sorted staticmethod str "
    + "sum super tuple type vars zip __import__ Exception ValueError TypeError KeyError "
    + "IndexError RuntimeError StopIteration AttributeError NotImplementedError OSError "
    + "PermissionError FileNotFoundError").split(" ")
);

const TOKEN_RE =
  /(#[^\n]*)|("""[\s\S]*?"""|'''[\s\S]*?'''|[frbFRB]{0,2}"(?:\\.|[^"\\\n])*"|[frbFRB]{0,2}'(?:\\.|[^'\\\n])*')|(@[A-Za-z_]\w*)|(\b(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.[\d_]*)?(?:[eE][+-]?\d+)?)\b)|([A-Za-z_]\w*)|([+\-*/%=<>!&|^~]+)/g;

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };

function esc(text) {
  return text.replace(/[&<>]/g, (ch) => ESCAPES[ch]);
}

export function highlightPython(code) {
  let html = "";
  let last = 0;
  let expectName = false;

  for (const match of code.matchAll(TOKEN_RE)) {
    const [token, comment, string, decorator, number, ident, operator] = match;
    if (match.index > last) html += esc(code.slice(last, match.index));

    let cls = "";
    if (comment) {
      cls = "tok-com";
    } else if (string) {
      cls = "tok-str";
    } else if (decorator) {
      cls = "tok-dec";
    } else if (number) {
      cls = "tok-num";
    } else if (ident) {
      if (KEYWORDS.has(token)) {
        cls = "tok-kw";
        expectName = token === "def" || token === "class";
      } else if (expectName) {
        cls = "tok-fn";
        expectName = false;
      } else if (token === "self" || token === "cls") {
        cls = "tok-self";
      } else if (BUILTINS.has(token)) {
        cls = "tok-bi";
      }
    } else if (operator) {
      cls = "tok-op";
    }

    html += cls ? `<span class="${cls}">${esc(token)}</span>` : esc(token);
    last = match.index + token.length;
  }

  html += esc(code.slice(last));
  return html;
}
