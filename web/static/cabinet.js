const $ = (id) => document.getElementById(id);

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
    card.appendChild(name);
    card.appendChild(who);
    box.appendChild(card);
  }
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
