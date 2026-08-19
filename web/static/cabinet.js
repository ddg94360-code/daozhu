const $ = (id) => document.getElementById(id);
let lastStages = [];

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

function li(text) {
  const el = document.createElement("li");
  el.textContent = text;
  return el;
}

function render(preview) {
  $("cabinet-rule").textContent = preview.rule || "";
  $("cabinet-chair").textContent = preview.chair || "";
  $("cabinet-disc").textContent = preview.disclaimer || "";
  $("cabinet-core").replaceChildren();
  $("cabinet-adjunct").replaceChildren();
  for (const m of preview.core || []) $("cabinet-core").appendChild(li(`${m.name}　${m.role}`));
  for (const m of preview.adjunct || []) $("cabinet-adjunct").appendChild(li(`${m.name}　${m.role}`));
  const box = $("cabinet-stages");
  box.replaceChildren();
  const h = document.createElement("h2");
  h.textContent = "五階段";
  box.appendChild(h);
  for (const s of preview.stages || []) {
    const card = document.createElement("div");
    card.className = "card stage-card";
    const name = document.createElement("h2");
    name.textContent = s.name;
    const who = document.createElement("p");
    who.className = "who";
    who.textContent = s.who || "";
    const body = document.createElement("p");
    body.className = "body";
    body.textContent = s.body || "";
    card.appendChild(name);
    card.appendChild(who);
    card.appendChild(body);
    box.appendChild(card);
  }
  lastStages = preview.stages || [];
}

$("cabinet-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("cabinet-err").textContent = "";
  try {
    const fd = new FormData(ev.target);
    render(await send("POST", "/api/cabinet/preview", { topic: fd.get("topic") }));
  } catch (e) {
    $("cabinet-err").textContent = e.message;
  }
});

$("cabinet-convene").addEventListener("click", async () => {
  $("cabinet-err").textContent = "";
  try {
    const topic = new FormData($("cabinet-form")).get("topic");
    render(await send("POST", "/api/cabinet/convene", {
      topic,
      persist: $("cabinet-persist").checked,
      depth: $("cabinet-depth").value,
    }));
  } catch (e) {
    $("cabinet-err").textContent = e.message;
  }
});

$("cabinet-followup-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("cabinet-followup-err").textContent = "";
  try {
    const topic = new FormData($("cabinet-form")).get("topic");
    const payload = {
      topic,
      name: $("cabinet-followup-name").value,
      question: $("cabinet-followup-q").value,
    };
    if (lastStages.length && lastStages.some((s) => String(s.body || "").trim())) {
      payload.stages = lastStages;
    }
    const data = await send("POST", "/api/cabinet/followup", payload);
    const box = $("cabinet-followup");
    box.hidden = false;
    box.replaceChildren();
    const h = document.createElement("h2");
    h.textContent = `${data.name}　追問`;
    const q = document.createElement("p");
    q.className = "who";
    q.textContent = data.question || "";
    const body = document.createElement("p");
    body.className = "body";
    body.textContent = data.body || "";
    box.appendChild(h);
    box.appendChild(q);
    box.appendChild(body);
  } catch (e) {
    $("cabinet-followup-err").textContent = e.message;
  }
});
