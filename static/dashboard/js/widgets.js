"use strict";

/* ═══════════════════════════════════════════════════════════════════════
   Codeforces rating chart + submission heatmap.
   
   This file's only remaining job is drawing the two visualizations —
   Chart.js still runs client-side, but reads data the template already
   embedded via Django's json_script filter, instead of calling an API.
   ═══════════════════════════════════════════════════════════════════════ */

function readJsonScript(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (err) {
    console.warn(`Could not parse JSON script #${id}:`, err.message);
    return null;
  }
}

/* ── Codeforces rating line chart ────────────────────────────────────── */

function buildRatingChart(history) {
  const canvas = document.getElementById("cf-rating-chart");
  // No canvas means the template already rendered the "No rating history
  // yet." message instead (see index.html) — nothing to draw.
  if (!canvas || !history || history.length === 0) return;

  const labels = history.map((h) => h.date_label);
  const ratings = history.map((h) => h.rating);

  // Use CSS variable values for colours
  const rust = "#b85c30";
  const rustLight = "#e8c8a8";
  const inkFaint = "#a89070";
  const border = "#d6c9b2";

  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: ratings,
        borderColor: rust,
        backgroundColor: rustLight + "55",
        borderWidth: 2,
        pointRadius: history.length > 20 ? 2 : 4,
        pointBackgroundColor: rust,
        pointBorderColor: "#f5efe3",
        pointBorderWidth: 1.5,
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => history[items[0].dataIndex]?.contest_name || "",
            label: (item) => `Rating: ${item.raw}`,
          },
          backgroundColor: "#1c130a",
          titleColor: "#f5efe3",
          bodyColor: "#e8c8a8",
          padding: 10,
          cornerRadius: 6,
        },
      },
      scales: {
        x: {
          ticks: { color: inkFaint, font: { size: 10 }, maxTicksLimit: 6 },
          grid: { color: border + "88" },
          border: { color: border },
        },
        y: {
          ticks: { color: inkFaint, font: { size: 10 } },
          grid: { color: border + "88" },
          border: { color: border },
        },
      },
    },
  });
}

/* ── Codeforces submission heatmap (last 26 weeks) ───────────────────── */

function buildHeatmap(cells) {
  const container = document.getElementById("cf-heatmap");
  if (!container || !cells) return;

  // The day-by-day grid (date, count, level 0-5) is precomputed server-side
  // now (see codeforces_service._build_heatmap) — this just renders it.
  container.innerHTML = "";
  cells.forEach((cell) => {
    const el = document.createElement("div");
    el.className = "cf-heatmap__cell";
    if (cell.level > 0) el.dataset.count = cell.level;
    el.title = `${cell.date}: ${cell.count} submission${cell.count !== 1 ? "s" : ""}`;
    container.appendChild(el);
  });
}

/* ═══════════════════════════════════════════════════════════════════════
   Bootstrap
   ═══════════════════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  buildRatingChart(readJsonScript("cf-rating-history-data"));
  buildHeatmap(readJsonScript("cf-heatmap-data"));
});