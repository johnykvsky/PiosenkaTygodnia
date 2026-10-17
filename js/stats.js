(function () {
  "use strict";

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const rootEl = document.getElementById("stats-root");
    if (!rootEl) return;

    const data = window.PIOSENKA_DATA || [];

    // 1. Collect artist play counts & unique tracks
    const artistStatsMap = new Map(); // key: primaryArtist -> { artist, count, tracks: [] }
    const uniqueArtistsSet = new Set();

    data.forEach((t) => {
      const artName = (t.primaryArtist || t.artist || "").trim();
      if (artName) {
        uniqueArtistsSet.add(artName);
        if (!artistStatsMap.has(artName)) {
          artistStatsMap.set(artName, {
            artist: artName,
            plays: 0,
            tracks: [],
          });
        }
        const entry = artistStatsMap.get(artName);
        entry.plays += 1;
        entry.tracks.push(t.title);
      }
    });

    // --- STAT 1: Decades (Tracks by release decade) ---
    const decadesMap = new Map();
    data.forEach((t) => {
      const yrNum = parseInt(t.releaseYear, 10);
      if (!isNaN(yrNum) && yrNum > 1900) {
        const dec = Math.floor(yrNum / 10) * 10;
        decadesMap.set(dec, (decadesMap.get(dec) || 0) + 1);
      }
    });
    const decadesList = Array.from(decadesMap.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([dec, count]) => ({
        decade: `${dec}s`,
        labelPl: dec >= 2000 ? `Lata ${dec}–${dec + 9}` : `Lata ${String(dec).slice(2)}. (${dec}s)`,
        count,
      }));
    const maxDecadeCount = Math.max(1, ...decadesList.map((d) => d.count));

    // --- STAT 2: Release Years (Roczniki Płyt) ---
    const yearsMap = new Map();
    data.forEach((t) => {
      if (t.releaseYear) {
        yearsMap.set(t.releaseYear, (yearsMap.get(t.releaseYear) || 0) + 1);
      }
    });
    const yearsListChrono = Array.from(yearsMap.entries())
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .map(([year, count]) => ({ year, count }));
    const yearsListByCount = [...yearsListChrono].sort(
      (a, b) => b.count - a.count || Number(a.year) - Number(b.year)
    );
    const maxYearCount = Math.max(1, ...yearsListChrono.map((y) => y.count));

    // --- STAT 3: Most Frequent Artists (Najczęstsi wykonawcy, plays > 1) ---
    const mostPlayedArtists = Array.from(artistStatsMap.values())
      .filter((a) => a.plays > 1)
      .sort((a, b) => b.plays - a.plays || a.artist.localeCompare(b.artist, "pl"));
    const maxArtistPlays = Math.max(1, ...mostPlayedArtists.map((a) => a.plays));

    // --- STAT 4: Music Genres (Gatunki muzyczne) ---
    const genreMap = new Map();
    data.forEach((t) => {
      const g = t.genre || "Inne";
      genreMap.set(g, (genreMap.get(g) || 0) + 1);
    });
    const genreList = Array.from(genreMap.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "pl"))
      .map(([genre, count]) => ({
        genre,
        count,
        pct: ((count / Math.max(1, data.length)) * 100).toFixed(1),
      }));
    const maxGenreCount = Math.max(1, ...genreList.map((g) => g.count));

    // KPI Summary Calculations
    const totalSongs = data.length;
    const totalUniqueArtists = uniqueArtistsSet.size;
    const totalMs = data.reduce((acc, t) => acc + (Number(t.durationMs) || (Number(t.durationSeconds) || 0) * 1000), 0);
    const totalSeconds = Math.round(totalMs / 1000);
    const totalMinutesRounded = Math.round(totalMs / 60000);

    function formatDaysHoursMinSec(sec) {
      const days = Math.floor(sec / 86400);
      const rem1 = sec % 86400;
      const hours = Math.floor(rem1 / 3600);
      const rem2 = rem1 % 3600;
      const minutes = Math.floor(rem2 / 60);
      const seconds = rem2 % 60;
      return `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }

    const formattedTotalTime = formatDaysHoursMinSec(totalSeconds);

    function renderYearsChart(sortMode) {
      const list = sortMode === "count" ? yearsListByCount : yearsListChrono;
      return list
        .map((item) => {
          const pct = Math.round((item.count / maxYearCount) * 100);
          return `
            <a href="index.html?albumYear=${encodeURIComponent(item.year)}" class="year-bar-row" title="Kliknij, aby zobaczyć utwory z płyt wydanych w roku ${escapeHtml(item.year)}">
              <span class="year-bar-label">${escapeHtml(item.year)}</span>
              <div class="year-bar-track">
                <div class="year-bar-fill" style="width: ${pct}%"></div>
              </div>
              <span class="year-bar-value">${item.count}</span>
            </a>
          `;
        })
        .join("");
    }

    rootEl.innerHTML = `
      <!-- KPI Summary Cards (3 general stats requested) -->
      <div class="stats-kpi-grid">
        <div class="kpi-card">
          <span class="kpi-value">${totalSongs}</span>
          <span class="kpi-label">Utworów na playliście</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-value">${totalUniqueArtists}</span>
          <span class="kpi-label">Unikalnych wykonawców</span>
        </div>
        <div class="kpi-card" title="Dokładny czas trwania: ${formattedTotalTime}">
          <span class="kpi-value">${String(totalMinutesRounded).replace(/\B(?=(\d{3})+(?!\d))/g, " ")}</span>
          <span class="kpi-label">Minut muzyki łącznie</span>
        </div>
      </div>

      <!-- Section Tabs -->
      <div class="stats-tabs" role="tablist" aria-label="Kategorie statystyk">
        <button type="button" class="stats-tab active" data-tab="all">Wszystkie</button>
        <button type="button" class="stats-tab" data-tab="decades">1. Dekady</button>
        <button type="button" class="stats-tab" data-tab="years">2. Roczniki płyt</button>
        <button type="button" class="stats-tab" data-tab="artists">3. Najczęstsi wykonawcy</button>
        <button type="button" class="stats-tab" data-tab="genres">4. Gatunki muzyczne</button>
      </div>

      <div class="stats-sections">
        <!-- 1. DECADES GRAPH -->
        <section class="stats-card" data-section="decades">
          <div class="stats-card-header">
            <div>
              <h2>1. Dekady</h2>
              <p class="stats-subtitle">Liczba utworów według dekady wydania albumu</p>
            </div>
          </div>
          <div class="decade-chart">
            ${decadesList
              .map((d) => {
                const pct = Math.round((d.count / maxDecadeCount) * 100);
                const share = ((d.count / Math.max(1, totalSongs)) * 100).toFixed(1);
                return `
                  <div class="chart-row">
                    <div class="chart-label-col">
                      <span class="chart-label-main">${escapeHtml(d.decade)}</span>
                      <span class="chart-label-sub">${escapeHtml(d.labelPl)}</span>
                    </div>
                    <div class="chart-bar-wrap">
                      <div class="chart-bar-fill" style="width: ${pct}%"></div>
                    </div>
                    <div class="chart-value-col">
                      <strong>${d.count}</strong>
                      <span class="chart-pct">(${share}%)</span>
                    </div>
                  </div>
                `;
              })
              .join("")}
          </div>
        </section>

        <!-- 4. GENRES GRAPH -->
        <section class="stats-card" data-section="genres">
          <div class="stats-card-header">
            <div>
              <h2>4. Gatunki muzyczne</h2>
              <p class="stats-subtitle">Podział ${totalSongs} utworów według gatunku muzycznego (kliknij gatunek, aby filtrować listę)</p>
            </div>
          </div>
          <div class="genre-chart">
            ${genreList
              .map((g) => {
                const pct = Math.round((g.count / maxGenreCount) * 100);
                return `
                  <a href="index.html?genre=${encodeURIComponent(g.genre)}" class="chart-row chart-row-link" title="Zobacz utwory z gatunku: ${escapeHtml(g.genre)}">
                    <div class="chart-label-col">
                      <span class="chart-label-main">${escapeHtml(g.genre)}</span>
                    </div>
                    <div class="chart-bar-wrap">
                      <div class="chart-bar-fill genre-bar-fill" style="width: ${pct}%"></div>
                    </div>
                    <div class="chart-value-col">
                      <strong>${g.count}</strong>
                      <span class="chart-pct">(${g.pct}%)</span>
                    </div>
                  </a>
                `;
              })
              .join("")}
          </div>
        </section>

        <!-- 2. RELEASE YEARS GRAPH -->
        <section class="stats-card stats-card-full" data-section="years">
          <div class="stats-card-header">
            <div>
              <h2>2. Roczniki płyt</h2>
              <p class="stats-subtitle">Liczba utworów z płyt wydanych w danym roku (kliknij słupek, aby wyświetlić utwory z tego rocznika)</p>
            </div>
            <div class="sort-toggle-group">
              <button type="button" class="btn-sort active" data-year-sort="chrono">Wg roku</button>
              <button type="button" class="btn-sort" data-year-sort="count">Wg liczby utworów</button>
            </div>
          </div>
          <div id="years-chart-container" class="years-chart-grid">
            ${renderYearsChart("chrono")}
          </div>
        </section>

        <!-- 3. MOST PLAYED ARTISTS LIST -->
        <section class="stats-card stats-card-full" data-section="artists">
          <div class="stats-card-header">
            <div>
              <h2>3. Najczęstsi wykonawcy</h2>
              <p class="stats-subtitle">Wykonawcy, którzy pojawili się na playliście więcej niż 1 raz (${mostPlayedArtists.length} wykonawców)</p>
            </div>
          </div>
          <div class="ranked-list ranked-list-grid">
            ${mostPlayedArtists
              .map((item, idx) => {
                const pct = Math.round((item.plays / maxArtistPlays) * 100);
                return `
                  <a href="index.html?artist=${encodeURIComponent(item.artist)}" class="ranked-item" title="Zobacz utwory wykonawcy: ${escapeHtml(item.artist)} (${escapeHtml(item.tracks.join(", "))})">
                    <span class="rank-num">${idx + 1}.</span>
                    <div class="ranked-main">
                      <div class="ranked-top-row">
                        <span class="ranked-title">${escapeHtml(item.artist)}</span>
                        <span class="ranked-meta">${escapeHtml(item.tracks.slice(0, 2).join(", "))}${item.tracks.length > 2 ? "…" : ""}</span>
                      </div>
                      <div class="ranked-bar-track">
                        <div class="ranked-bar-fill" style="width: ${pct}%"></div>
                      </div>
                    </div>
                    <span class="rank-count-badge">${item.plays}×</span>
                  </a>
                `;
              })
              .join("")}
          </div>
        </section>
      </div>
    `;

    // Tab switching logic
    const tabBtns = rootEl.querySelectorAll(".stats-tab");
    const sections = rootEl.querySelectorAll("[data-section]");
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-tab");
        tabBtns.forEach((b) => b.classList.toggle("active", b === btn));
        sections.forEach((sec) => {
          if (target === "all") {
            sec.style.display = "";
            sec.classList.remove("stats-card-single");
          } else {
            const match = sec.getAttribute("data-section") === target;
            sec.style.display = match ? "" : "none";
            sec.classList.toggle("stats-card-single", match);
          }
        });
      });
    });

    // Release Year sort toggle
    const sortBtns = rootEl.querySelectorAll("[data-year-sort]");
    const yearsContainer = document.getElementById("years-chart-container");
    sortBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-year-sort");
        sortBtns.forEach((b) => b.classList.toggle("active", b === btn));
        yearsContainer.innerHTML = renderYearsChart(mode);
      });
    });
  });
})();
