const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));

const copyIcon = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14h11V7H8v14h11V7z"/></svg>';
const search = document.querySelector("#search");
const category = document.querySelector("#filter-category");
const teamFilter = document.querySelector("#filter-team");
const count = document.querySelector("#result-count");
const grid = document.querySelector("#grid");
const empty = document.querySelector("#empty");

function renderCard(item) {
  const projectCommand = item.installCommand;
  const globalCommand = projectCommand.replace("apm install ", "apm install -g ");
  const teamBadge = item.team ? `<span class="badge badge-team">${escapeHtml(item.team)}</span>` : "";
  const installRow = (label, command) => `<div class="install-row"><label>${label}</label><code>${escapeHtml(command)}</code><button class="copy-btn" type="button" data-copy="${escapeHtml(command)}" aria-label="Copy ${label} install command">${copyIcon}</button></div>`;
  const searchText = [item.name, item.description, item.author, item.team].filter(Boolean).join(" ").toLowerCase();
  return `<article class="card" data-category="${escapeHtml(item.category)}" data-team="${escapeHtml(item.team || "")}" data-search="${escapeHtml(searchText)}"><header class="card-header"><h3>${escapeHtml(item.name)}</h3><span class="badge badge-${escapeHtml(item.category)}">${escapeHtml(item.category)}</span>${teamBadge}</header><p class="card-description">${escapeHtml(item.description)}</p><dl class="card-meta"><div><dt>Version</dt><dd>${escapeHtml(item.version)}</dd></div><div><dt>Author</dt><dd>${escapeHtml(item.author)}</dd></div><div><dt>License</dt><dd>${escapeHtml(item.license)}</dd></div></dl><div class="install-block">${installRow("Project", projectCommand)}${installRow("Global", globalCommand)}</div></article>`;
}

function applyFilters() {
  const query = search.value.trim().toLowerCase();
  const selectedCategory = category.value;
  const selectedTeam = teamFilter.value;
  let visibleCount = 0;
  grid.querySelectorAll(".card").forEach((card) => {
    const visible = (!query || card.dataset.search.includes(query))
      && (!selectedCategory || card.dataset.category === selectedCategory)
      && (!selectedTeam || card.dataset.team === selectedTeam);
    card.classList.toggle("hidden", !visible);
    if (visible) visibleCount += 1;
  });
  count.textContent = `${visibleCount} package${visibleCount === 1 ? "" : "s"}`;
  empty.classList.toggle("visible", visibleCount === 0);
}

function setStat(id, value) {
  document.querySelector(id).textContent = value;
}

fetch("catalog.json", { cache: "no-cache" })
  .then((response) => {
    if (!response.ok) throw new Error(`Catalog request failed: ${response.status}`);
    return response.json();
  })
  .then((catalog) => {
    const items = Array.isArray(catalog.items) ? catalog.items : [];
    setStat("#stat-packages", catalog.itemCount ?? items.length);
    setStat("#stat-agents", catalog.categories?.agents ?? 0);
    setStat("#stat-skills", catalog.categories?.skills ?? 0);
    setStat("#stat-instructions", catalog.categories?.instructions ?? 0);
    setStat("#stat-teams", catalog.teams?.length ?? 0);
    teamFilter.insertAdjacentHTML("beforeend", (catalog.teams || []).map((team) => `<option value="${escapeHtml(team)}">${escapeHtml(team)}</option>`).join(""));
    document.querySelector("#last-updated").textContent = catalog.lastUpdated || "latest release";
    grid.innerHTML = items.map(renderCard).join("");
    applyFilters();
  })
  .catch((error) => {
    console.error(error);
    empty.textContent = "Catalog unavailable.";
    empty.classList.add("visible");
  });

[search, category, teamFilter].forEach((element) => element.addEventListener("input", applyFilters));
grid.addEventListener("click", (event) => {
  const button = event.target.closest(".copy-btn");
  if (!button || !navigator.clipboard) return;
  navigator.clipboard.writeText(button.dataset.copy).then(() => {
    button.classList.add("copied");
    setTimeout(() => button.classList.remove("copied"), 1200);
  });
});

const guide = document.querySelector("#install-guide");
document.querySelector("#open-guide").addEventListener("click", () => guide.showModal());
document.querySelector("#close-guide").addEventListener("click", () => guide.close());
guide.addEventListener("click", (event) => {
  if (event.target === guide) guide.close();
  const button = event.target.closest(".copy-command");
  if (!button || !navigator.clipboard) return;
  navigator.clipboard.writeText(button.dataset.copy).then(() => {
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = "Copy"; }, 1200);
  });
});
