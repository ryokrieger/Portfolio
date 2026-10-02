/*
 * widgets.js — draws the two Codeforces visuals on the portfolio page:
 *   1. the rating-history line chart (Chart.js)
 *   2. the 26-week submission heatmap (plain <div> cells)
 *
 * The data is NOT fetched here. Django fetches and caches it on the server and
 * embeds it in the page as two JSON blocks:
 *   #cf-rating-history-data  -> [{ contest_name, date_label, rating }, ...]
 *   #cf-heatmap-data         -> [{ date: "YYYY-MM-DD", count, level }, ...]
 * so the browser never calls the Codeforces API itself.
 */
(function () {
  "use strict";

  // Colours match the CSS design tokens in style.css
  var RUST = "#b85c30";
  var RUST_TINT = "rgba(184, 92, 48, 0.12)";
  var INK_MUTED = "#6b5740";
  var BORDER = "#d6c9b2";

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  // "2026-09-14" -> "Sep 14, 2026" (parsed by hand so timezones can't shift the day)
  function prettyDate(iso) {
    var parts = iso.split("-");
    var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }

  // ── 1. Rating history chart ───────────────────────────────────────────────
  function renderRatingChart() {
    var canvas = document.getElementById("cf-rating-chart");
    if (!canvas) return; // template shows "No rating history yet." instead

    var history = readJSON("cf-rating-history-data") || [];
    if (!history.length) return;

    if (typeof Chart === "undefined") {
      // Chart.js failed to load (offline / blocked CDN): fail quietly.
      canvas.parentElement.innerHTML =
        '<p class="cf-chart-empty">Rating chart unavailable right now.</p>';
      return;
    }

    new Chart(canvas, {
      type: "line",
      data: {
        labels: history.map(function (p) { return p.date_label; }),
        datasets: [{
          data: history.map(function (p) { return p.rating; }),
          borderColor: RUST,
          backgroundColor: RUST_TINT,
          borderWidth: 2,
          fill: true,
          tension: 0.25,
          pointRadius: history.length > 40 ? 0 : 3,
          pointHoverRadius: 5,
          pointBackgroundColor: RUST
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: function (items) {
                return history[items[0].dataIndex].contest_name;
              },
              label: function (ctx) {
                return "Rating " + ctx.parsed.y + "  (" + history[ctx.dataIndex].date_label + ")";
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: INK_MUTED, font: { size: 10 }, maxTicksLimit: 6, maxRotation: 0 }
          },
          y: {
            grid: { color: BORDER },
            ticks: { color: INK_MUTED, font: { size: 10 }, maxTicksLimit: 5 }
          }
        }
      }
    });
  }

  // ── 2. Submission heatmap ─────────────────────────────────────────────────
  function renderHeatmap() {
    var grid = document.getElementById("cf-heatmap");
    if (!grid) return;

    var cells = readJSON("cf-heatmap-data") || [];
    if (!cells.length) {
      grid.style.display = "block";
      grid.innerHTML = '<p class="cf-chart-empty">No submission data yet.</p>';
      return;
    }

    // Days run Sunday -> Saturday down each column, so columns = days / 7 (rounded up).
    grid.style.gridTemplateColumns = "repeat(" + Math.ceil(cells.length / 7) + ", 1fr)";

    var total = 0;
    var fragment = document.createDocumentFragment();
    cells.forEach(function (cell) {
      total += cell.count;
      var div = document.createElement("div");
      div.className = "cf-heatmap__cell";
      div.dataset.count = String(cell.level); // style.css colours levels 1-5
      div.title =
        (cell.count === 1 ? "1 submission" : cell.count + " submissions") +
        " on " + prettyDate(cell.date);
      fragment.appendChild(div);
    });
    grid.appendChild(fragment);

    grid.setAttribute("role", "img");
    grid.setAttribute(
      "aria-label",
      "Codeforces submission activity over the last 26 weeks: " + total + " submissions"
    );
  }

  renderRatingChart();
  renderHeatmap();
})();