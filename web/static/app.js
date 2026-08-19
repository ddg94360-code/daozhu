const $ = (id) => document.getElementById(id);

async function get(path) {
  const r = await fetch(path);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

async function send(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

function li(text, cls) {
  const el = document.createElement("li");
  if (cls) el.className = cls;
  el.textContent = text;
  return el;
}

async function refreshAll() {
  const [ov, ex, he, re, sh, mo, no, pe, de, dz] = await Promise.all([
    get("/api/overview"),
    get("/api/expenses"),
    get("/api/health"),
    get("/api/reminders"),
    get("/api/shopping"),
    get("/api/moods"),
    get("/api/notes"),
    get("/api/perception"),
    get("/api/decisions"),
    get("/api/daozang"),
  ]);
  renderWeek(ov);
  renderPerception(pe);
  renderExpenses(ex);
  renderHealth(he);
  renderReminders(re);
  renderShopping(sh);
  renderMoods(mo);
  renderNotes(no);
  renderDecisions(de);
  renderDaozang(dz);
}

function renderWeek(ov) {
  $("solar").textContent = ov.solar_term.guide || "";
  $("memory-dir").textContent = ov.memory_dir || "";
  const r = ov.report;
  const cur = r.currency || "";
  const mood = r.mood_trend || {};
  $("week").replaceChildren();
  const lines = [
    `近七日 ${r.period || ""}`,
    `支出 ${cur}${r.expense_total}　睡眠均 ${r.sleep_avg_hours}h　運動 ${r.exercise_count} 次`,
    `情緒 正${mood["正向"] || 0} 中${mood["中性"] || 0} 負${mood["負向"] || 0}　待複習 ${r.study_notes_due}　決策 ${r.decisions_logged}`,
    r.energy_insight || "",
  ];
  if (r.care_flag) lines.push("最近幾天感覺不太好。");
  for (const t of lines) $("week").appendChild(Object.assign(document.createElement("p"), { textContent: t }));
}

function renderExpenses(ex) {
  const s = ex.summary;
  const cats = Object.entries(s.by_category || {}).map(([k, v]) => `${k} ${s.currency || ""}${v}`).join("　");
  $("expense-summary").textContent = `${s.month} 合計 ${s.currency || ""}${s.total}　${cats}`;
  $("expense-list").replaceChildren();
  for (const rec of ex.recent || []) {
    $("expense-list").appendChild(li(`${rec.date}　${rec.item}　${rec.category}　${rec.amount}`));
  }
}

function renderHealth(he) {
  $("health-list").replaceChildren();
  for (const rec of he.records || []) {
    $("health-list").appendChild(li(`${rec.date}　睡${rec.sleep_hours || "—"}　${rec.exercise || "—"}　${rec.water || "—"}`));
  }
}

function renderReminders(re) {
  const recs = [...(re.records || [])].sort((a, b) => Number(b.due) - Number(a.due));
  $("reminder-list").replaceChildren();
  for (const rec of recs) {
    const row = li(`${rec.datetime}　${rec.content}`, rec.due ? "due" : "");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "完成";
    btn.addEventListener("click", async () => {
      try {
        await send("POST", `/api/reminders/${rec.id}/done`);
        $("reminder-err").textContent = "";
        renderReminders(await get("/api/reminders"));
      } catch (e) {
        $("reminder-err").textContent = e.message;
      }
    });
    row.appendChild(btn);
    $("reminder-list").appendChild(row);
  }
}

function renderShopping(sh) {
  $("shopping-open").replaceChildren();
  $("shopping-done").replaceChildren();
  for (const rec of sh.records || []) {
    const row = li(rec.item);
    const check = document.createElement("button");
    check.type = "button";
    check.textContent = "勾";
    check.addEventListener("click", async () => {
      try {
        await send("POST", `/api/shopping/${rec.id}/check`);
        $("shopping-err").textContent = "";
        renderShopping(await get("/api/shopping"));
      } catch (e) {
        $("shopping-err").textContent = e.message;
      }
    });
    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "刪";
    del.addEventListener("click", async () => {
      try {
        await send("DELETE", `/api/shopping/${rec.id}`);
        $("shopping-err").textContent = "";
        renderShopping(await get("/api/shopping"));
      } catch (e) {
        $("shopping-err").textContent = e.message;
      }
    });
    if (!rec.checked) row.appendChild(check);
    row.appendChild(del);
    (rec.checked ? $("shopping-done") : $("shopping-open")).appendChild(row);
  }
}

function renderMoods(mo) {
  $("mood-list").replaceChildren();
  for (const rec of mo.records || []) {
    $("mood-list").appendChild(li(`${rec.date}　${rec.classification}　${rec.mood}`));
  }
}

function renderNotes(no) {
  $("notes-due").replaceChildren();
  $("notes-recent").replaceChildren();
  for (const rec of no.due || []) $("notes-due").appendChild(noteRow(rec, true));
  for (const rec of no.recent || []) $("notes-recent").appendChild(noteRow(rec, false));
}

function noteRow(rec, due) {
  const text = due
    ? `到期　${rec.subject}　${rec.summary || rec.original}`
    : `${rec.subject}　${rec.summary || rec.original}`;
  const row = li(text, due ? "due" : "");
  if (!rec.id) return row;
  if (due) {
    const rev = document.createElement("button");
    rev.type = "button";
    rev.textContent = "複習";
    rev.addEventListener("click", async () => {
      try {
        await send("POST", `/api/notes/${rec.id}/reviewed`);
        $("note-err").textContent = "";
        renderNotes(await get("/api/notes"));
        renderWeek(await get("/api/overview"));
        renderPerception(await get("/api/perception"));
      } catch (e) {
        $("note-err").textContent = e.message;
      }
    });
    row.appendChild(rev);
  }
  const del = document.createElement("button");
  del.type = "button";
  del.textContent = "刪";
  del.addEventListener("click", async () => {
    try {
      await send("DELETE", `/api/notes/${rec.id}`);
      $("note-err").textContent = "";
      renderNotes(await get("/api/notes"));
      renderWeek(await get("/api/overview"));
      renderPerception(await get("/api/perception"));
    } catch (e) {
      $("note-err").textContent = e.message;
    }
  });
  row.appendChild(del);
  return row;
}

function renderPerception(pe) {
  const box = $("perception");
  if (!box) return;
  box.replaceChildren();
  for (const layer of pe.layers || []) {
    const el = document.createElement("span");
    el.className = layer.on ? "layer on" : "layer";
    el.textContent = layer.on && layer.hint ? `${layer.label}　${layer.hint}` : layer.label;
    box.appendChild(el);
  }
  const disc = document.createElement("p");
  disc.className = "disclaimer";
  disc.textContent = pe.disclaimer || "";
  box.appendChild(disc);
}

function renderDecisions(de) {
  $("decision-list").replaceChildren();
  for (const rec of de.records || []) {
    const reason = rec.reason ? `　${rec.reason}` : "";
    $("decision-list").appendChild(li(`${rec.timestamp}　${rec.topic}　${rec.verdict}${reason}`));
  }
}

function renderDaozang(dz) {
  const box = $("daozang");
  box.replaceChildren();
  const labels = { daoist: "道家", strategist: "縱橫家", legalist: "法家", confucian: "儒家" };
  const personae = dz.personae || {};
  for (const key of ["daoist", "confucian", "legalist", "strategist"]) {
    const block = document.createElement("div");
    block.className = "persona";
    const h = document.createElement("h3");
    h.textContent = labels[key] || key;
    block.appendChild(h);
    const ul = document.createElement("ul");
    const recs = (personae[key] && personae[key].records) || [];
    if (!recs.length) ul.appendChild(li("（空）"));
    for (const rec of recs) {
      ul.appendChild(li(`${rec.classify || ""}　${rec.adopted_strategy || ""}`));
    }
    block.appendChild(ul);
    box.appendChild(block);
  }
}

function bindForm(formId, errId, handler) {
  $(formId).addEventListener("submit", async (ev) => {
    ev.preventDefault();
    $(errId).textContent = "";
    try {
      await handler(new FormData(ev.target));
      ev.target.reset();
    } catch (e) {
      $(errId).textContent = e.message;
    }
  });
}

bindForm("expense-form", "expense-err", async (fd) => {
  const category = fd.get("category") || "";
  await send("POST", "/api/expenses", {
    item: fd.get("item"),
    amount: Number(fd.get("amount")),
    category,
  });
  renderExpenses(await get("/api/expenses"));
  renderWeek(await get("/api/overview"));
});

bindForm("health-form", "health-err", async (fd) => {
  const body = {};
  const sleep = fd.get("sleep_hours");
  if (sleep) body.sleep_hours = Number(sleep);
  if (fd.get("exercise")) body.exercise = fd.get("exercise");
  if (fd.get("water")) body.water = fd.get("water");
  await send("POST", "/api/health", body);
  renderHealth(await get("/api/health"));
  renderWeek(await get("/api/overview"));
});

bindForm("reminder-form", "reminder-err", async (fd) => {
  const raw = String(fd.get("datetime") || "");
  const iso = raw.length === 16 ? `${raw}:00` : raw;
  await send("POST", "/api/reminders", { content: fd.get("content"), datetime: iso });
  renderReminders(await get("/api/reminders"));
});

bindForm("shopping-form", "shopping-err", async (fd) => {
  await send("POST", "/api/shopping", { item: fd.get("item") });
  renderShopping(await get("/api/shopping"));
});

bindForm("mood-form", "mood-err", async (fd) => {
  const res = await send("POST", "/api/moods", { mood: fd.get("mood") });
  $("mood-care").textContent = res.care_note || "";
  renderMoods(await get("/api/moods"));
  renderWeek(await get("/api/overview"));
  renderPerception(await get("/api/perception"));
});

bindForm("note-form", "note-err", async (fd) => {
  await send("POST", "/api/notes", {
    subject: fd.get("subject"),
    content: fd.get("content"),
    review_days: Number(fd.get("review_days") || 7),
  });
  renderNotes(await get("/api/notes"));
  renderWeek(await get("/api/overview"));
  renderPerception(await get("/api/perception"));
});

bindForm("decision-form", "decision-err", async (fd) => {
  await send("POST", "/api/decisions", {
    topic: fd.get("topic"),
    verdict: fd.get("verdict"),
    reason: fd.get("reason") || "",
  });
  renderDecisions(await get("/api/decisions"));
  renderWeek(await get("/api/overview"));
  renderPerception(await get("/api/perception"));
});

function chatLine(who, text) {
  const el = document.createElement("li");
  el.textContent = `${who}　${text}`;
  return el;
}

bindForm("chat-form", "chat-err", async (fd) => {
  const text = String(fd.get("text") || "").trim();
  $("chat-log").appendChild(chatLine("你", text));
  const res = await send("POST", "/api/chat", { text });
  $("chat-log").appendChild(chatLine("樞", res.reply || ""));
  await refreshAll();
});

refreshAll().catch((e) => { $("week").textContent = e.message; });
