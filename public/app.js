const $ = (sel) => document.querySelector(sel);

const checkBtn = $("#checkBtn");
const exportBtn = $("#exportBtn");
const resultsEl = $("#results");
const statsEl = $("#stats");
const ipInput = $("#ipInput");
const timeoutEl = $("#timeout");
const workersEl = $("#workers");
const portsEl = $("#ports");

let lastResults = [];

// 🔧 Change this if backend is on a different deployment
// Example: "https://dot5-backend.vercel.app"
// If frontend + backend are in the SAME Vercel project → leave it as ""
const API_BASE = "";

/**
 * Parse pasted IP list
 */
function parseIPs(text) {
  return text
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

/**
 * Escape text for safe HTML
 */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[m]));
}

/**
 * Render results in the UI
 */
function renderResults(rows) {
  resultsEl.innerHTML = "";
  let real = 0, fake = 0;

  const header = document.createElement("div");
  header.className = "item";
  header.innerHTML = `
    <div class="code small"><strong>Input</strong></div>
    <div class="small"><strong>Status</strong></div>
    <div class="small"><strong>HTTP</strong></div>
    <div class="small"><strong>Proxy / Info</strong></div>
  `;
  resultsEl.appendChild(header);

  rows.forEach((r) => {
    if (r.status === "real") real++;
    else fake++;
    const d = document.createElement("div");
    d.className = "item";
    d.innerHTML = `
      <div class="code">${escapeHtml(r.input || "")}</div>
      <div><span class="status badge ${r.status}">${r.status.toUpperCase()}</span></div>
      <div class="small">${r.http_status ?? "-"}</div>
      <div class="small code" title="${r.final_url || ""}">
        ${escapeHtml(r.normalized_proxy || "")}
        ${r.elapsed_ms ? ` • ${r.elapsed_ms}ms` : ""}
        ${r.error ? ` • err: ${escapeHtml(r.error.slice(0,120))}` : ""}
      </div>
    `;
    resultsEl.appendChild(d);
  });

  statsEl.textContent = `Total: ${rows.length} • ✅ Real: ${real} • ❌ Fake: ${fake}`;
  exportBtn.disabled = rows.length === 0;
}

/**
 * Run check
 */
checkBtn.addEventListener("click", async () => {
  const ips = parseIPs(ipInput.value);
  if (ips.length === 0) {
    alert("Please paste IPs (IP or IP:PORT or user:pass@IP:PORT)");
    return;
  }

  resultsEl.innerHTML = "";
  statsEl.textContent = "Checking…";

  const timeout = parseFloat(timeoutEl.value || "6");
  const max_workers = parseInt(workersEl.value || "20", 10);
  const try_ports = portsEl.value
    .split(",")
    .map((v) => parseInt(v.trim(), 10))
    .filter((n) => !isNaN(n));

  try {
    const res = await fetch(`${API_BASE}/api/check-bulk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ips, timeout, max_workers, try_ports }),
    });
    const data = await res.json();
    lastResults = data;
    renderResults(data);
  } catch (e) {
    statsEl.textContent = "Error contacting server. Is DOT 5 running?";
    console.error(e);
  }
});

/**
 * Export results to CSV
 */
exportBtn.addEventListener("click", async () => {
  if (!lastResults.length) return;
  try {
    const res = await fetch(`${API_BASE}/api/export-csv`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ results: lastResults }),
    });
    const csv = await res.text();
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "dot5_results.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Error exporting CSV");
    console.error(e);
  }
});
