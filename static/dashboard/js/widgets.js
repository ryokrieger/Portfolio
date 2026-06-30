"use strict";

/* ═══════════════════════════════════════════════════════════════════════
   Utility: add / remove loading shimmer class
   ═══════════════════════════════════════════════════════════════════════ */

function setLoading(el, on) {
  if (!el) return;
  if (on) {
    el.classList.add("loading");
  } else {
    el.classList.remove("loading");
  }
}

/* ═══════════════════════════════════════════════════════════════════════
   1. GITHUB
   Reads [data-api-url] from each .repo-card, fetches the GitHub
   API, then fills in description, language, and star count.
   ═══════════════════════════════════════════════════════════════════════ */

async function loadGitHubRepos() {
  const cards = document.querySelectorAll(".repo-card[data-api-url]");
  if (!cards.length) return;

  const fetches = Array.from(cards).map(async (card) => {
    const apiUrl = card.dataset.apiUrl;
    const repoName = apiUrl.split("/").pop();

    const descEl = card.querySelector(`[data-repo-desc="${repoName}"]`);
    const langEl = card.querySelector(`[data-repo-lang="${repoName}"]`);
    const starEl = card.querySelector(`[data-repo="${repoName}"]`);

    // Only shimmer the live-fetched elements — description is already rendered
    [langEl, starEl].forEach((el) => setLoading(el, true));

    try {
      const res = await fetch(apiUrl, {
        headers: { Accept: "application/vnd.github+json" },
      });

      if (!res.ok) throw new Error(`GitHub API ${res.status}`);

      const data = await res.json();

      if (langEl) langEl.textContent = data.language || "";
      if (starEl) starEl.textContent = data.stargazers_count ?? "0";

    } catch (err) {
      console.warn(`GitHub: could not load ${repoName}:`, err.message);
      if (langEl) langEl.textContent = "";
      if (starEl) starEl.textContent = "—";
    } finally {
      [langEl, starEl].forEach((el) => setLoading(el, false));
    }
  });

  await Promise.allSettled(fetches);
}

/* ═══════════════════════════════════════════════════════════════════════
   2. CODEFORCES
   Calls two Codeforces API endpoints in parallel:
   - user.info → rating, maxRating, rank
   - user.status → count unique problems solved (verdict: OK)
   - user.rating → rating history for Chart.js line chart
   ═══════════════════════════════════════════════════════════════════════ */

async function loadCodeforcesStats() {
  const ratingEl = document.getElementById("cf-rating");
  const maxRatingEl = document.getElementById("cf-max-rating");
  const rankEl = document.getElementById("cf-rank");
  const solvedEl = document.getElementById("cf-solved");

  if (!ratingEl || !maxRatingEl || !rankEl || !solvedEl) return;

  const card = document.getElementById("codeforces-card");
  const handle = card?.dataset.cfHandle || "ryokrieger";

  [ratingEl, maxRatingEl, rankEl, solvedEl].forEach((el) => setLoading(el, true));

  try {
    const infoUrl = card?.dataset.cfInfoUrl || `https://codeforces.com/api/user.info?handles=${handle}`;
    const statusUrl = card?.dataset.cfStatusUrl || `https://codeforces.com/api/user.status?handle=${handle}&count=500`;
    const ratingUrl = `https://codeforces.com/api/user.rating?handle=${handle}`;

    const [infoRes, statusRes, ratingRes] = await Promise.all([
      fetch(infoUrl),
      fetch(statusUrl),
      fetch(ratingUrl),
    ]);

    // ── User info ──────────────────────────────────────────────────
    if (infoRes.ok) {
      const infoData = await infoRes.json();
      if (infoData.status === "OK") {
        const user = infoData.result[0];
        ratingEl.textContent = user.rating ?? "—";
        maxRatingEl.textContent = user.maxRating ?? "—";
        rankEl.textContent = user.rank ?? "—";
      }
    }

    // ── Problems solved + heatmap ──────────────────────────────────
    if (statusRes.ok) {
      const statusData = await statusRes.json();
      if (statusData.status === "OK") {
        const submissions = statusData.result;

        // Unique accepted problems
        const solved = new Set(
          submissions
            .filter((s) => s.verdict === "OK")
            .map((s) => `${s.problem.contestId}-${s.problem.index}`)
        );
        solvedEl.textContent = solved.size;

        // Build heatmap (last 26 weeks = 182 days)
        buildHeatmap(submissions);
      }
    }

    // ── Rating history chart ───────────────────────────────────────
    if (ratingRes.ok) {
      const ratingData = await ratingRes.json();
      if (ratingData.status === "OK") {
        buildRatingChart(ratingData.result);
      }
    }

  } catch (err) {
    console.warn("Codeforces API error:", err.message);
    [ratingEl, maxRatingEl, rankEl, solvedEl].forEach((el) => (el.textContent = "—"));
  } finally {
    [ratingEl, maxRatingEl, rankEl, solvedEl].forEach((el) => setLoading(el, false));
  }
}

/* ── Codeforces rating line chart ────────────────────────────────────── */

function buildRatingChart(contests) {
  const canvas = document.getElementById("cf-rating-chart");
  const emptyMsg = document.getElementById("cf-chart-empty");

  if (!canvas) return;

  if (!contests || contests.length === 0) {
    canvas.style.display = "none";
    if (emptyMsg) emptyMsg.style.display = "block";
    return;
  }

  const labels = contests.map((c) => {
    const d = new Date(c.ratingUpdateTimeSeconds * 1000);
    return d.toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  });

  const ratings = contests.map((c) => c.newRating);

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
        pointRadius: contests.length > 20 ? 2 : 4,
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
            title: (items) => contests[items[0].dataIndex]?.contestName || "",
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

function buildHeatmap(submissions) {
  const container = document.getElementById("cf-heatmap");
  if (!container) return;

  // Build a map of date string → submission count
  const countMap = {};
  const now = Date.now();
  const sixMonthsAgo = now - 26 * 7 * 24 * 60 * 60 * 1000;

  submissions.forEach((s) => {
    const ts = s.creationTimeSeconds * 1000;
    if (ts < sixMonthsAgo) return;
    const key = new Date(ts).toISOString().slice(0, 10); // YYYY-MM-DD
    countMap[key] = (countMap[key] || 0) + 1;
  });

  // Build 182 day grid starting from 26 weeks ago, aligned to Sunday
  const startDate = new Date(sixMonthsAgo);
  // Rewind to the nearest previous Sunday
  startDate.setDate(startDate.getDate() - startDate.getDay());
  startDate.setHours(0, 0, 0, 0);

  const cells = [];
  const cursor = new Date(startDate);

  while (cursor <= new Date(now)) {
    const key = cursor.toISOString().slice(0, 10);
    const count = countMap[key] || 0;
    const level = count === 0 ? 0 : count === 1 ? 1 : count <= 3 ? 2 : count <= 5 ? 3 : count <= 8 ? 4 : 5;

    const cell = document.createElement("div");
    cell.className = "cf-heatmap__cell";
    if (level > 0) cell.dataset.count = level;
    cell.title = `${key}: ${count} submission${count !== 1 ? "s" : ""}`;
    cells.push(cell);

    cursor.setDate(cursor.getDate() + 1);
  }

  container.innerHTML = "";
  cells.forEach((c) => container.appendChild(c));
}

/* ═══════════════════════════════════════════════════════════════════════
   Bootstrap
   ═══════════════════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  loadGitHubRepos();
  loadCodeforcesStats();
});