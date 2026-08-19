const $ = (id) => document.getElementById(id);

function looksIso(text) {
  return /^\d{4}-\d{2}-\d{2}/.test(text) && !text.startsWith("{");
}

function twoInts(text) {
  const m = text.match(/\d+/g);
  if (m && m.length >= 2) return [Number(m[0]), Number(m[1])];
  return [3, 8];
}

function dtLocalFrom(raw) {
  if (looksIso(raw)) return raw;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.dt_local === "string") return parsed.dt_local;
    const nested = parsed && parsed.input && parsed.input.dt_local;
    if (typeof nested === "string") return String(nested).replace(" ", "T");
  } catch {
    /* textarea 不是 JSON，就當沒有時刻 */
  }
  return "";
}

function yearInRange(n) {
  return Number.isInteger(n) && n >= 1900 && n <= 2100;
}

function parseTextarea(raw) {
  try {
    const parsed = JSON.parse(String(raw || "").trim());
    if (parsed && typeof parsed === "object") return parsed;
  } catch {
    /* textarea 不是 JSON */
  }
  return null;
}

function yearFrom(raw) {
  const text = String(raw || "").trim();
  const fallback = new Date().getFullYear();
  const parsed = parseTextarea(text);
  if (parsed) {
    if (yearInRange(Number(parsed.year))) return Number(parsed.year);
    const nested = parsed.input && parsed.input.year;
    if (yearInRange(Number(nested))) return Number(nested);
  }
  const iso = dtLocalFrom(text);
  if (iso) {
    const y = Number(iso.slice(0, 4));
    if (yearInRange(y)) return y;
  }
  const m = text.match(/\d{4}/);
  if (m) {
    const y = Number(m[0]);
    if (yearInRange(y)) return y;
  }
  return fallback;
}

function genderFrom(raw) {
  const parsed = parseTextarea(raw);
  if (!parsed) return "";
  const g = parsed.gender || (parsed.input && parsed.input.gender);
  const s = String(g || "").trim();
  if (s === "男" || s === "女") return s;
  return "";
}

async function get(path) {
  const r = await fetch(path);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

get("/api/xinjing/status").then((st) => {
  $("xinjing-status").textContent = st.tianji ? `已接天機　${st.dir}` : "未接天機";
}).catch((e) => {
  $("xinjing-status").textContent = e.message;
});

$("xinjing-cast").addEventListener("click", async () => {
  $("xinjing-err").textContent = "";
  try {
    const mode = $("xinjing-mode").value;
    const extra = {};
    const raw = ($("xinjing-data").value || "").trim();
    if (mode === "gua") extra.question = raw.slice(0, 80);
    if (mode === "fengshui") {
      extra.year = yearFrom(raw);
      const g = genderFrom(raw);
      if (g) extra.gender = g;
    }
    if (mode === "chart" || mode === "bazi" || mode === "ziwei" || mode === "qimen" || mode === "qizheng" || mode === "numerology" || mode === "fusion") {
      extra.dt_local = dtLocalFrom(raw);
    }
    if (mode === "meihua") extra.numbers = twoInts(raw);
    if (mode === "xingming") {
      extra.question = raw.slice(0, 80);
      extra.name = raw.slice(0, 80);
    }
    extra.question = extra.question || raw.slice(0, 80);
    const r = await fetch("/api/xinjing/cast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, ...extra }),
    });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.message || r.statusText);
    $("xinjing-data").value = JSON.stringify(body.data, null, 2);
    const playMode = ["bazi", "ziwei", "meihua", "qimen", "xingming", "numerology", "fusion"].includes(body.mode)
      ? "gua"
      : (body.mode === "qizheng" ? "chart" : (body.mode === "lenormand" ? "tarot" : body.mode));
    const play = await fetch("/api/xinjing/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: playMode, data: body.data }),
    });
    if (!play.ok) {
      const err = await play.json().catch(() => ({}));
      throw new Error(err.message || play.statusText);
    }
    $("xinjing-stage").srcdoc = await play.text();
  } catch (e) {
    $("xinjing-err").textContent = e.message;
  }
});

$("xinjing-example").addEventListener("click", async () => {
  $("xinjing-err").textContent = "";
  try {
    const mode = $("xinjing-mode").value;
    const data = await get(`/api/xinjing/examples/${mode}`);
    $("xinjing-data").value = JSON.stringify(data, null, 2);
  } catch (e) {
    $("xinjing-err").textContent = e.message;
  }
});

$("xinjing-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("xinjing-err").textContent = "";
  try {
    const mode = $("xinjing-mode").value;
    let data;
    try {
      data = JSON.parse($("xinjing-data").value || "{}");
    } catch {
      throw new Error("資料須為 JSON 物件");
    }
    const r = await fetch("/api/xinjing/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, data }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.message || r.statusText);
    }
    $("xinjing-stage").srcdoc = await r.text();
  } catch (e) {
    $("xinjing-err").textContent = e.message;
  }
});
