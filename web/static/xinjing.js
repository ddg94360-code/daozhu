const $ = (id) => document.getElementById(id);

async function get(path) {
  const r = await fetch(path);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

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
