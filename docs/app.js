const WEEKDAY_LABELS = {
  mon: "월요일",
  tue: "화요일",
  wed: "수요일",
  thu: "목요일",
  fri: "금요일",
  sat: "토요일",
  sun: "일요일",
};

const state = {
  catalog: [],
  trackedIds: new Set(),
  selectedIds: new Set(),
  activeWeekday: "all",
  search: "",
  trackedOnly: false,
};

const grid = document.getElementById("grid");
const template = document.getElementById("cardTemplate");
const searchInput = document.getElementById("search");
const weekdayFilters = document.getElementById("weekdayFilters");
const selectedCount = document.getElementById("selectedCount");
const createIssueButton = document.getElementById("createIssue");
const clearSelectionButton = document.getElementById("clearSelection");
const viewAllButton = document.getElementById("viewAll");
const viewTrackedButton = document.getElementById("viewTracked");

function getRepoContext() {
  const owner = window.location.hostname.split(".")[0];
  const repo = window.location.pathname.split("/").filter(Boolean)[0] || "";
  return { owner, repo };
}

function issueUrlForRequest(entries, action) {
  const { owner, repo } = getRepoContext();
  const issueBase = `https://github.com/${owner}/${repo}/issues/new`;
  const payload = { action, title_ids: entries.map((entry) => entry.title_id) };
  const titles = entries.map((entry) => `- ${entry.title_name} (${entry.title_id})`).join("\n");
  const body = [
    action === "remove" ? "Visual catalog removal request." : "Visual catalog subscription request.",
    "",
    titles,
    "",
    `<!-- subscription-request ${JSON.stringify(payload)} -->`,
  ].join("\n");
  const params = new URLSearchParams({
    title: action === "remove"
      ? `Remove ${entries.length} webtoon${entries.length > 1 ? "s" : ""}`
      : `Track ${entries.length} webtoon${entries.length > 1 ? "s" : ""}`,
    labels: "subscription-request",
    body,
  });
  return `${issueBase}?${params.toString()}`;
}

function updateSelectionUI() {
  const selectedEntries = state.catalog.filter((entry) => state.selectedIds.has(entry.title_id));
  const trackedCount = selectedEntries.filter((entry) => state.trackedIds.has(entry.title_id)).length;
  const untrackedCount = selectedEntries.length - trackedCount;

  selectedCount.textContent = String(state.selectedIds.size);

  if (selectedEntries.length === 0) {
    createIssueButton.disabled = true;
    createIssueButton.textContent = "추가하기";
    return;
  }

  if (trackedCount > 0 && untrackedCount > 0) {
    createIssueButton.disabled = true;
    createIssueButton.textContent = "추가/제거는 따로 선택";
    return;
  }

  createIssueButton.disabled = false;
  createIssueButton.textContent = trackedCount > 0 ? "제거하기" : "추가하기";
}

function buildWeekdayFilters() {
  const weekdays = [{ code: "all", label: "전체" }, ...Object.entries(WEEKDAY_LABELS).map(([code, label]) => ({ code, label }))];
  weekdayFilters.innerHTML = "";
  weekdays.forEach(({ code, label }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `weekday-chip${state.activeWeekday === code ? " active" : ""}`;
    button.textContent = label;
    button.addEventListener("click", () => {
      state.activeWeekday = code;
      buildWeekdayFilters();
      render();
    });
    weekdayFilters.appendChild(button);
  });
}

function filteredCatalog() {
  return state.catalog.filter((entry) => {
    const weekdayMatches = state.activeWeekday === "all" || entry.weekday === state.activeWeekday;
    const searchMatches = !state.search || entry.title_name.toLowerCase().includes(state.search.toLowerCase());
    const trackedMatches = !state.trackedOnly || state.trackedIds.has(entry.title_id);
    return weekdayMatches && searchMatches && trackedMatches;
  });
}

function updateViewFilterUI() {
  viewAllButton.classList.toggle("active", !state.trackedOnly);
  viewTrackedButton.classList.toggle("active", state.trackedOnly);
}

function render() {
  grid.innerHTML = "";
  const entries = filteredCatalog();

  entries.forEach((entry) => {
    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector(".card");
    const button = fragment.querySelector(".card-button");
    const image = fragment.querySelector(".thumb");
    const title = fragment.querySelector(".title");
    const weekday = fragment.querySelector(".weekday");
    const tracked = fragment.querySelector(".tracked");
    const meta = fragment.querySelector(".meta");
    image.src = entry.thumbnail_url || "";
    image.alt = entry.title_name;
    title.textContent = entry.title_name;
    weekday.textContent = WEEKDAY_LABELS[entry.weekday] || entry.weekday;
    meta.textContent = `ID ${entry.title_id}`;

    const isTracked = state.trackedIds.has(entry.title_id);
    if (isTracked) {
      tracked.classList.remove("hidden");
    }

    if (state.selectedIds.has(entry.title_id)) {
      card.classList.add("selected");
    }

    button.addEventListener("click", () => {
      if (state.selectedIds.has(entry.title_id)) {
        state.selectedIds.delete(entry.title_id);
        card.classList.remove("selected");
      } else {
        state.selectedIds.add(entry.title_id);
        card.classList.add("selected");
      }
      updateSelectionUI();
    });

    grid.appendChild(fragment);
  });
}

async function loadData() {
  const cacheBust = `v=${Date.now()}`;
  const [catalogResponse, trackedResponse] = await Promise.all([
    fetch(`./catalog.json?${cacheBust}`, { cache: "no-store" }),
    fetch(`./tracked.json?${cacheBust}`, { cache: "no-store" }),
  ]);
  const [catalogPayload, trackedPayload] = await Promise.all([
    catalogResponse.json(),
    trackedResponse.json(),
  ]);
  state.catalog = catalogPayload.webtoons || [];
  state.trackedIds = new Set(trackedPayload.title_ids || []);
}

searchInput.addEventListener("input", (event) => {
  state.search = event.target.value.trim();
  render();
});

clearSelectionButton.addEventListener("click", () => {
  state.selectedIds.clear();
  updateSelectionUI();
  render();
});

viewAllButton.addEventListener("click", () => {
  state.trackedOnly = false;
  updateViewFilterUI();
  render();
});

viewTrackedButton.addEventListener("click", () => {
  state.trackedOnly = true;
  updateViewFilterUI();
  render();
});

createIssueButton.addEventListener("click", () => {
  const selectedEntries = state.catalog.filter((entry) => state.selectedIds.has(entry.title_id));
  if (!selectedEntries.length) {
    return;
  }
  const trackedCount = selectedEntries.filter((entry) => state.trackedIds.has(entry.title_id)).length;
  const action = trackedCount > 0 ? "remove" : "add";
  window.open(issueUrlForRequest(selectedEntries, action), "_blank", "noopener,noreferrer");
});

loadData()
  .then(() => {
    buildWeekdayFilters();
    updateSelectionUI();
    updateViewFilterUI();
    render();
  })
  .catch((error) => {
    grid.innerHTML = `<p>카탈로그를 불러오지 못했습니다: ${error.message}</p>`;
  });
