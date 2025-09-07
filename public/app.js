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

function parseIPs(text) {
  return text.split(/\r?\n/).map(x => x.trim()).filter(x => x.length > 0);
}

function renderResults(rows) {
  resultsEl.innerHTML = "";
  let real = 0, fake = 0;

  // Header row
  const header = document.createElement("div");
  header.className = "item header";
  header.innerHTML = `
    <div>
      <span class="code small"><strong>Input</strong></span>
      <span class="small"><strong>Status</strong></span>
    </div>
    <div>
      <span class="small"><strong>HTTP</strong></span>
      <span class="small"><strong>Info</strong></span>
    </div>
    <div>
      <span class="small"><strong>Ports</strong></span>
      <span class="small"><strong>Origin</strong></span>
    </div>
    <div>
      <span class="small"><strong>Fake Source</strong></span>
    </div>
  `;
  resultsEl.appendChild(header);

  rows.forEach(r => {
    if (r.status === "real") real++; else fake++;

    const d = document.createElement("div");
    d.className = "item";

    // Format fake source as styled button with tooltip
    let fakeSourceDisplay = "-";
    if (r.status === "fake" && r.fake_source_url) {
      const siteName = getSiteNameFromUrl(r.fake_source_url);
      fakeSourceDisplay = `
        <a href="${escapeHtml(r.fake_source_url)}" 
           target="_blank" 
           class="fake-source-btn" 
           title="${escapeHtml(r.fake_source_url)}">
          🌐 ${escapeHtml(siteName)}
        </a>`;
    }

    // Format info section: latency + error
    const infoContent = `
      ${r.elapsed_ms ? `<span class="latency">${r.elapsed_ms}ms</span>` : ""}
      ${r.error ? `<span class="error">⚠️ ${escapeHtml(r.error.slice(0,80))}</span>` : ""}
    `;

    d.innerHTML = `
      <div>
        <span class="code">${escapeHtml(r.input || "")}</span>
        <span><span class="status badge ${r.status}">${r.status.toUpperCase()}</span></span>
      </div>
      <div>
        <span class="small">${r.http_status ?? "-"}</span>
        <span class="info">${infoContent}</span>
      </div>
      <div>
        <span class="small code">${r.ports_tried ? r.ports_tried.join(", ") : "-"}</span>
        <span class="small">${escapeHtml(r.source || "-")}</span>
      </div>
      <div>
        <span class="small">${fakeSourceDisplay}</span>
      </div>
    `;
    resultsEl.appendChild(d);
  });

  statsEl.textContent = `Total: ${rows.length} • ✅ Real: ${real} • ❌ Fake: ${fake}`;
  exportBtn.disabled = rows.length === 0;
}

function getSiteNameFromUrl(url) {
  try {
    const hostname = new URL(url).hostname;
    if (hostname.includes("proxyscrape")) return "ProxyScrape";
    if (hostname.includes("free-proxy-list")) return "Free Proxy List";
    if (hostname.includes("proxynova")) return "ProxyNova";
    if (hostname.includes("hidemy.name")) return "HideMy.name";
    if (hostname.includes("spys.one")) return "Spys.one";
    return hostname.replace("www.", "").split(".")[0];
  } catch (e) {
    return "Unknown Source";
  }
}

function escapeHtml(s) {
  if (typeof s !== "string") return String(s);
  return s.replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "<",
    ">": ">",
    "\"": "&quot;",
    "'": "&#39;"
  }[m]));
}

checkBtn.addEventListener("click", async () => {
  const ips = parseIPs(ipInput.value);
  if (!ips.length) {
    alert("Please paste IPs");
    return;
  }
  resultsEl.innerHTML = "";
  statsEl.textContent = "Checking…";

  const timeout = parseFloat(timeoutEl.value || "6");
  const max_workers = parseInt(workersEl.value || "20", 10);
  const try_ports = portsEl.value.split(",").map(v => parseInt(v.trim(),10)).filter(n => !isNaN(n));

  try {
    const res = await fetch("/api/check-bulk", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ ips, timeout, max_workers, try_ports })
    });
    const data = await res.json();
    lastResults = data;
    renderResults(data);
  } catch (e) {
    statsEl.textContent = "Error contacting server";
    console.error(e);
  }
});

exportBtn.addEventListener("click", async () => {
  if (!lastResults.length) return;
  const res = await fetch("/api/export-csv", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ results: lastResults })
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
});