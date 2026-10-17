(function () {
  "use strict";

  const VINYL_SVG = `
    <svg class="cover-fallback" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2.5"/>
      <circle cx="32" cy="32" r="22" stroke="currentColor" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>
      <circle cx="32" cy="32" r="16" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>
      <circle cx="32" cy="32" r="9" stroke="currentColor" stroke-width="2"/>
      <circle cx="32" cy="32" r="3" fill="currentColor"/>
    </svg>
  `;

  // Normalize string for diacritic-insensitive and case-insensitive comparison
  function normalizeStr(str) {
    if (!str) return "";
    const plMap = {
      ą: "a", ć: "c", ę: "e", ł: "l", ń: "n", ó: "o", ś: "s", ź: "z", ż: "z",
      Ą: "a", Ć: "c", Ę: "e", Ł: "l", Ń: "n", Ó: "o", Ś: "s", Ź: "z", Ż: "z",
    };
    return String(str)
      .replace(/[’‘]/g, "'")
      .replace(/[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]/g, (ch) => plMap[ch] || ch)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Highlight matching substring (supports Polish diacritics in original text)
  function highlightMatch(text, query) {
    if (!text) return "";
    if (!query || !query.trim()) return escapeHtml(text);

    const normText = normalizeStr(text);
    const normQuery = normalizeStr(query.trim());
    if (!normQuery) return escapeHtml(text);

    const idx = normText.indexOf(normQuery);
    if (idx === -1) return escapeHtml(text);

    const before = text.slice(0, idx);
    const match = text.slice(idx, idx + normQuery.length);
    const after = text.slice(idx + normQuery.length);
    return `${escapeHtml(before)}<mark class="hl">${escapeHtml(match)}</mark>${escapeHtml(after)}`;
  }

  function formatDuration(sec) {
    const s = Math.max(0, Number(sec) || 0);
    const mins = Math.floor(s / 60);
    const rem = String(s % 60).padStart(2, "0");
    return `${mins}:${rem}`;
  }

  // Theme management
  function getSavedTheme() {
    try {
      const fromStorage = localStorage.getItem("pt_theme");
      if (fromStorage === "light" || fromStorage === "dark") return fromStorage;
    } catch (_) {}
    return "dark";
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem("pt_theme", theme);
    } catch (_) {}
  }

  const initialTheme = getSavedTheme();
  document.documentElement.setAttribute("data-theme", initialTheme);

  function initTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || getSavedTheme();
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeBtn(currentTheme);

    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        saveTheme(next);
        updateThemeBtn(next);
      });
    }
  }

  function updateThemeBtn(theme) {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.textContent = theme === "dark" ? "☀️ Jasny motyw" : "🌙 Ciemny motyw";
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();

    const listEl = document.getElementById("tracks-list");
    if (!listEl) return;

    const data = window.PIOSENKA_DATA || [];

    const inputArtist = document.getElementById("filter-artist");
    const inputSong = document.getElementById("filter-song");
    const inputAlbum = document.getElementById("filter-album");
    const inputAlbumYear = document.getElementById("filter-album-year");
    const selectGenre = document.getElementById("filter-genre");
    const btnReset = document.getElementById("btn-reset-filters");
    const btnSortDesc = document.getElementById("btn-sort-desc");
    const btnSortAsc = document.getElementById("btn-sort-asc");
    const resultsCountEl = document.getElementById("results-count");
    const activeTagsEl = document.getElementById("active-tags");

    // Default sort order: descending (from latest added #604 down to #1)
    let sortDirection = "desc";

    // Populate Genre options
    const genresSet = new Set();
    data.forEach((t) => {
      if (t.genre) genresSet.add(t.genre);
    });

    const genres = Array.from(genresSet).sort((a, b) => a.localeCompare(b, "pl"));
    genres.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = g;
      opt.textContent = g;
      selectGenre.appendChild(opt);
    });

    function getFilterState() {
      return {
        artist: inputArtist.value.trim(),
        song: inputSong.value.trim(),
        album: inputAlbum.value.trim(),
        albumYear: inputAlbumYear.value.trim(),
        genre: selectGenre.value.trim(),
      };
    }

    function doesTrackMatch(track, state) {
      if (state.artist) {
        const q = normalizeStr(state.artist);
        if (!normalizeStr(track.artist).includes(q)) {
          return false;
        }
      }
      if (state.song) {
        const q = normalizeStr(state.song);
        if (!normalizeStr(track.title).includes(q)) {
          return false;
        }
      }
      if (state.album) {
        const q = normalizeStr(state.album);
        if (!normalizeStr(track.album).includes(q)) {
          return false;
        }
      }
      if (state.albumYear) {
        if (track.releaseYear !== state.albumYear) {
          return false;
        }
      }
      if (state.genre) {
        if (track.genre !== state.genre) {
          return false;
        }
      }
      return true;
    }

    function renderActiveTags(state) {
      activeTagsEl.innerHTML = "";
      const tags = [];

      if (state.artist) {
        tags.push({
          label: `Wykonawca: "${state.artist}"`,
          clear: () => { inputArtist.value = ""; render(); },
        });
      }
      if (state.song) {
        tags.push({
          label: `Utwór: "${state.song}"`,
          clear: () => { inputSong.value = ""; render(); },
        });
      }
      if (state.album) {
        tags.push({
          label: `Album: "${state.album}"`,
          clear: () => { inputAlbum.value = ""; render(); },
        });
      }
      if (state.albumYear) {
        tags.push({
          label: `Rok wydania: ${state.albumYear}`,
          clear: () => { inputAlbumYear.value = ""; render(); },
        });
      }
      if (state.genre) {
        tags.push({
          label: `Gatunek: ${state.genre}`,
          clear: () => { selectGenre.value = ""; render(); },
        });
      }

      tags.forEach((t) => {
        const span = document.createElement("span");
        span.className = "filter-tag";
        span.innerHTML = `${escapeHtml(t.label)} <button type="button" title="Usuń filtr" aria-label="Usuń filtr">&times;</button>`;
        span.querySelector("button").addEventListener("click", t.clear);
        activeTagsEl.appendChild(span);
      });

      inputArtist.classList.toggle("is-active", Boolean(state.artist));
      inputSong.classList.toggle("is-active", Boolean(state.song));
      inputAlbum.classList.toggle("is-active", Boolean(state.album));
      inputAlbumYear.classList.toggle("is-active", Boolean(state.albumYear));
      selectGenre.classList.toggle("is-active", Boolean(state.genre));

      btnReset.disabled = tags.length === 0;
    }

    function render() {
      const state = getFilterState();
      renderActiveTags(state);

      const hasFilter = Boolean(
        state.artist || state.song || state.album || state.albumYear || state.genre
      );

      const filtered = data
        .filter((t) => doesTrackMatch(t, state))
        .sort((a, b) => (sortDirection === "desc" ? b.order - a.order : a.order - b.order));

      const totalFilteredSeconds = filtered.reduce(
        (acc, t) => acc + (Number(t.durationSeconds) || 0),
        0
      );
      const totalFilteredMins = Math.round(totalFilteredSeconds / 60);

      if (hasFilter) {
        resultsCountEl.innerHTML = `Znaleziono <strong>${filtered.length}</strong> z ${data.length} utworów (czas: <strong>${totalFilteredMins} min</strong>)`;
      } else {
        resultsCountEl.innerHTML = `Wyświetlono wszystkie <strong>${filtered.length}</strong> utwory`;
      }

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state">
            <h3>Brak utworów spełniających kryteria</h3>
            <p>Spróbuj zmienić wpisane frazy lub wyczyścić filtry.</p>
          </div>
        `;
        return;
      }

      const htmlParts = filtered.map((t) => {
        const coverHtml = t.cover
          ? `<img src="${escapeHtml(t.cover)}" alt="Okładka: ${escapeHtml(t.artist)} - ${escapeHtml(t.album)}" loading="lazy" />`
          : VINYL_SVG;

        const yearPillClasses = ["album-year-pill"];
        if (state.albumYear && t.releaseYear === state.albumYear) {
          yearPillClasses.push("is-matched-year");
        }
        const yearBadge = t.releaseYear
          ? `<button type="button" class="${yearPillClasses.join(" ")}" data-release-year="${escapeHtml(t.releaseYear)}" title="Filtruj utwory z płyt wydanych w roku ${escapeHtml(t.releaseYear)}">${escapeHtml(t.releaseYear)}</button>`
          : "";

        const genreTagClasses = ["album-genre-tag"];
        if (state.genre && t.genre === state.genre) {
          genreTagClasses.push("is-matched-genre");
        }
        const genreBadge = t.genre
          ? `<button type="button" class="${genreTagClasses.join(" ")}" data-genre="${escapeHtml(t.genre)}" title="Filtruj według gatunku: ${escapeHtml(t.genre)}">${escapeHtml(t.genre)}</button>`
          : "";

        const durFormatted = formatDuration(t.durationSeconds);

        return `
          <article class="track-card">
            <div class="track-order" title="Pozycja na playliście Spotify">
              <span class="order-hash">#</span><span class="order-num">${t.order}</span>
            </div>

            <div class="cover-wrap">
              ${coverHtml}
            </div>

            <div class="track-main">
              <div class="track-title-row">
                <span class="track-title">${highlightMatch(t.title, state.song)}</span>
              </div>
              <div class="track-artist-row">
                <button type="button" class="album-artist-btn" data-artist="${escapeHtml(t.primaryArtist || t.artist)}" title="Filtruj wykonawcę: ${escapeHtml(t.primaryArtist || t.artist)}">
                  ${highlightMatch(t.artist, state.artist)}
                </button>
              </div>
            </div>

            <div class="track-album-col">
              <div class="track-album-label">Album</div>
              <button type="button" class="track-album-btn" data-album="${escapeHtml(t.album)}" title="Filtruj album: ${escapeHtml(t.album)}">
                ${highlightMatch(t.album, state.album)}
              </button>
            </div>

            <div class="track-meta-col">
              <div class="track-badges-row">
                ${yearBadge}
                ${genreBadge}
              </div>
              <div class="track-duration-row">
                <span class="track-duration" title="Czas trwania utworu">⏱ ${durFormatted}</span>
                ${t.spotifyUrl ? `<a href="${escapeHtml(t.spotifyUrl)}" target="_blank" rel="noopener noreferrer" class="track-spotify-link" title="Odsłuchaj w Spotify">▶ Spotify</a>` : ""}
              </div>
            </div>
          </article>
        `;
      });

      listEl.innerHTML = htmlParts.join("");
    }

    // Filter event listeners
    inputArtist.addEventListener("input", render);
    inputSong.addEventListener("input", render);
    inputAlbum.addEventListener("input", render);
    inputAlbumYear.addEventListener("input", () => {
      const cleaned = inputAlbumYear.value.replace(/[^0-9]/g, "").slice(0, 4);
      if (inputAlbumYear.value !== cleaned) {
        inputAlbumYear.value = cleaned;
      }
      render();
    });
    selectGenre.addEventListener("change", render);

    btnReset.addEventListener("click", () => {
      inputArtist.value = "";
      inputSong.value = "";
      inputAlbum.value = "";
      inputAlbumYear.value = "";
      selectGenre.value = "";
      render();
    });

    function setSortDirection(dir) {
      sortDirection = dir;
      btnSortDesc.classList.toggle("active", dir === "desc");
      btnSortAsc.classList.toggle("active", dir === "asc");
      render();
    }

    if (btnSortDesc) {
      btnSortDesc.addEventListener("click", () => setSortDirection("desc"));
    }
    if (btnSortAsc) {
      btnSortAsc.addEventListener("click", () => setSortDirection("asc"));
    }

    // Delegate clicks on interactive pills inside track cards
    listEl.addEventListener("click", (e) => {
      const relYearBtn = e.target.closest("[data-release-year]");
      if (relYearBtn) {
        const yr = relYearBtn.getAttribute("data-release-year");
        inputAlbumYear.value = inputAlbumYear.value.trim() === yr ? "" : yr;
        render();
        return;
      }

      const artistBtn = e.target.closest("[data-artist]");
      if (artistBtn) {
        const art = artistBtn.getAttribute("data-artist");
        inputArtist.value = normalizeStr(inputArtist.value.trim()) === normalizeStr(art) ? "" : art;
        render();
        return;
      }

      const albumBtn = e.target.closest("[data-album]");
      if (albumBtn) {
        const alb = albumBtn.getAttribute("data-album");
        inputAlbum.value = normalizeStr(inputAlbum.value.trim()) === normalizeStr(alb) ? "" : alb;
        render();
        return;
      }

      const genreBtn = e.target.closest("[data-genre]");
      if (genreBtn) {
        const g = genreBtn.getAttribute("data-genre");
        selectGenre.value = selectGenre.value === g ? "" : g;
        render();
      }
    });

    // Main view tab switching (Lista utworów <-> Statystyki)
    const viewTracks = document.getElementById("view-tracks");
    const viewStats = document.getElementById("view-stats");
    const mainNavLinks = document.querySelectorAll(".nav-link[data-main-tab]");

    function switchMainTab(tabName) {
      const isStats = tabName === "stats";
      if (viewTracks) viewTracks.hidden = isStats;
      if (viewStats) viewStats.hidden = !isStats;

      mainNavLinks.forEach((link) => {
        const active = link.getAttribute("data-main-tab") === (isStats ? "stats" : "tracks");
        link.classList.toggle("active", active);
        if (active) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      });

      document.title = isStats
        ? "Piosenka Tygodnia — Statystyki"
        : "Piosenka Tygodnia — Katalog utworów";
    }

    document.querySelectorAll("[data-main-tab]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        const targetTab = el.getAttribute("data-main-tab");
        switchMainTab(targetTab);
        const newHash = targetTab === "stats" ? "#statystyki" : "#utwory";
        if (window.location.hash !== newHash) {
          try {
            history.replaceState(null, "", newHash);
          } catch (_) {}
        }
      });
    });

    // Delegate clicks on filter links inside Statystyki (e.g. href="index.html?artist=...")
    const statsRoot = document.getElementById("stats-root");
    if (statsRoot) {
      statsRoot.addEventListener("click", (e) => {
        const link = e.target.closest('a[href^="index.html?"]');
        if (!link) return;
        e.preventDefault();

        const queryStr = link.getAttribute("href").split("?")[1] || "";
        const qParams = new URLSearchParams(queryStr);

        inputArtist.value = qParams.get("artist") || "";
        inputSong.value = qParams.get("song") || "";
        inputAlbum.value = qParams.get("album") || "";
        inputAlbumYear.value = (qParams.get("albumYear") || "").replace(/[^0-9]/g, "");
        selectGenre.value = qParams.get("genre") || "";

        render();
        switchMainTab("tracks");
        try {
          history.replaceState(null, "", "#utwory");
        } catch (_) {}
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    // Apply URL query parameters or hash if present on initial load
    const params = new URLSearchParams(window.location.search);
    if (params.get("artist")) inputArtist.value = params.get("artist");
    if (params.get("song")) inputSong.value = params.get("song");
    if (params.get("album")) inputAlbum.value = params.get("album");
    if (params.get("albumYear")) inputAlbumYear.value = params.get("albumYear").replace(/[^0-9]/g, "");
    if (params.get("genre")) selectGenre.value = params.get("genre");

    if (window.location.hash === "#statystyki") {
      switchMainTab("stats");
    }

    // Initial render
    render();
  });
})();
