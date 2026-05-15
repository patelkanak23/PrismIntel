// SSE connection and DOM updates only
const API = "";

const btn = document.getElementById("research-btn");
const progressCard = document.getElementById("progress-card");
const riskCard = document.getElementById("risk-card");
const reportCard = document.getElementById("report-card");
const statusText = document.getElementById("status-text");
const progressFill = document.getElementById("progress-fill");
const reportBody = document.getElementById("report-body");
const reportTitle = document.getElementById("report-title");
const historyList = document.getElementById("history-list");

let currentReport = "";
let currentEventSource = null;

document.addEventListener("DOMContentLoaded", loadHistory);

btn.addEventListener("click", async () => {
  const company = document.getElementById("company-name").value.trim();
  if (!company) {
    alert("Please enter a company name");
    return;
  }

  const payload = {
    company_name: company,
    website_url: document.getElementById("website-url").value.trim(),
    hq_location: document.getElementById("hq-location").value.trim(),
    industry: document.getElementById("industry").value.trim()
  };

  btn.disabled = true;
  btn.textContent = "Researching...";
  show(progressCard);
  hide(riskCard);
  hide(reportCard);
  resetChecklist();
  setProgress(0);
  resetSpinner();
  statusText.textContent = "Starting research...";

  try {
    const res = await fetch(`${API}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    openSSE(data.job_id, company);
  } catch (error) {
    statusText.textContent = "❌ Backend not running";
    btn.disabled = false;
    btn.textContent = "🔍 Research Company";
  }
});

function openSSE(jobId, company) {
  if (currentEventSource) currentEventSource.close();
  currentEventSource = new EventSource(`${API}/research/${jobId}/stream`);

  currentEventSource.onmessage = (event) => {
    if (!event.data || event.data.startsWith(":")) return;
    try {
      const msg = JSON.parse(event.data);
      handleEvent(msg, company, currentEventSource);
    } catch (error) {
      statusText.textContent = "Received an unreadable update";
    }
  };

  currentEventSource.onerror = () => {
    currentEventSource.close();
    statusText.textContent = "❌ Connection lost";
    btn.disabled = false;
    btn.textContent = "🔍 Research Company";
  };
}

function handleEvent(msg, company, eventSource) {
  const type = msg.type;
  const data = msg.data || {};

  if (type === "progress") {
    statusText.textContent = data.message || "Working...";
    if (data.pct !== undefined) setProgress(data.pct);
  } else if (type === "briefing_complete") {
    markChecklistDone(data.category);
    setProgress(75);
  } else if (type === "risk_score") {
    showRiskScores(data.scores || {});
    setProgress(88);
  } else if (type === "competitor_analysis" || type === "competitors_done") {
    setProgress(94);
  } else if (type === "complete") {
    eventSource.close();
    setProgress(100);
    stopSpinner();
    statusText.textContent = "✅ Research complete!";
    currentReport = data.report || "";
    reportTitle.textContent = `Intelligence Report: ${company}`;
    renderMarkdown(currentReport);
    show(reportCard);
    btn.disabled = false;
    btn.textContent = "🔍 Research Company";
    loadHistory();
  } else if (type === "error") {
    eventSource.close();
    statusText.textContent = `❌ ${data.message || "Research failed"}`;
    btn.disabled = false;
    btn.textContent = "🔍 Research Company";
  }
}

function renderMarkdown(markdown) {
  let html = escapeHtml(markdown)
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^- (.+)$/gm, "<li>$1</li>");

  html = html.split("\n\n").map((block) => {
    const trimmed = block.trim();
    if (!trimmed) return "";
    if (/^<(h[123]|li|ul)/.test(trimmed)) return trimmed;
    return `<p>${trimmed.replace(/\n/g, "<br>")}</p>`;
  }).join("\n");

  html = html.replace(/(<li>.*?<\/li>\s*)+/gs, (match) => `<ul>${match}</ul>`);
  reportBody.innerHTML = html;
}

function showRiskScores(scores) {
  show(riskCard);
  const map = {
    overall: "overall_risk",
    financial: "financial_risk",
    reputational: "reputational_risk",
    market: "market_risk"
  };

  Object.entries(map).forEach(([key, field]) => {
    const value = scores[field] || 0;
    const valueEl = document.getElementById(`val-${key}`);
    const boxEl = document.getElementById(`risk-${key}`);
    if (valueEl) valueEl.textContent = value || "—";
    if (boxEl) {
      boxEl.classList.remove("risk-low", "risk-medium", "risk-high");
      boxEl.classList.add(value <= 4 ? "risk-low" : value <= 7 ? "risk-medium" : "risk-high");
    }
  });
}

async function loadHistory() {
  try {
    const res = await fetch(`${API}/history`);
    const data = await res.json();
    const history = data.history || [];
    historyList.innerHTML = "";

    if (history.length === 0) {
      historyList.innerHTML = '<p class="sidebar-empty">No research yet</p>';
      return;
    }

    history.forEach((item) => {
      const div = document.createElement("div");
      div.textContent = item.company_name || "Untitled research";
      div.title = item.created_at || "";
      div.addEventListener("click", () => loadPastReport(item.job_id));
      historyList.appendChild(div);
    });
  } catch (error) {
    historyList.innerHTML = '<p class="sidebar-empty">No research yet</p>';
  }
}

async function loadPastReport(jobId) {
  if (!jobId) return;
  const res = await fetch(`${API}/research/${jobId}/report`);
  const data = await res.json();
  if (data.report) {
    currentReport = data.report;
    renderMarkdown(currentReport);
    reportTitle.textContent = "Intelligence Report";
    show(reportCard);
  }
}

document.getElementById("pdf-btn").addEventListener("click", async () => {
  const res = await fetch(`${API}/generate-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown: currentReport })
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "prismintel_report.pdf";
  link.click();
  URL.revokeObjectURL(url);
});

document.getElementById("copy-btn").addEventListener("click", () => {
  navigator.clipboard.writeText(currentReport);
  const copyBtn = document.getElementById("copy-btn");
  copyBtn.textContent = "✅ Copied!";
  setTimeout(() => {
    copyBtn.textContent = "📋 Copy";
  }, 2000);
});

document.getElementById("new-btn").addEventListener("click", () => {
  hide(progressCard);
  hide(riskCard);
  hide(reportCard);
  setProgress(0);
  resetChecklist();
  resetSpinner();
  currentReport = "";
  document.getElementById("company-name").value = "";
  document.getElementById("website-url").value = "";
  document.getElementById("hq-location").value = "";
  document.getElementById("industry").value = "";
  statusText.textContent = "Initializing...";
});

function show(element) {
  element.classList.remove("hidden");
}

function hide(element) {
  element.classList.add("hidden");
}

function setProgress(percent) {
  progressFill.style.width = `${Math.max(0, Math.min(100, percent))}%`;
}

function markChecklistDone(category) {
  const element = document.getElementById(`check-${category}`);
  if (!element) return;
  element.textContent = `✅ ${element.textContent.slice(2).trim()}`;
  element.classList.add("done");
}

function resetChecklist() {
  const labels = {
    company: "Company Research",
    financial: "Financial Analysis",
    industry: "Industry Analysis",
    news: "News Scan"
  };

  Object.entries(labels).forEach(([key, label]) => {
    const element = document.getElementById(`check-${key}`);
    if (element) {
      element.textContent = `⬜ ${label}`;
      element.classList.remove("done");
    }
  });
}

function stopSpinner() {
  document.getElementById("spinner").style.animation = "none";
}

function resetSpinner() {
  document.getElementById("spinner").style.animation = "";
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
