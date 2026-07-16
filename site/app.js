const state = { packages: [], owner: "generic", query: "" };

const ownerFilter = document.querySelector("#owner-filter");
const search = document.querySelector("#search");
const packageGrid = document.querySelector("#packages");
const empty = document.querySelector("#empty");

function render() {
  const filtered = state.packages.filter((pkg) => {
    const text = `${pkg.name} ${pkg.description} ${pkg.owner} ${pkg.skills.join(" ")} ${pkg.agents.join(" ")}`.toLowerCase();
    return pkg.owner === state.owner && text.includes(state.query.toLowerCase());
  });
  document.querySelector("#result-heading").textContent = `${state.owner[0].toUpperCase()}${state.owner.slice(1)} packages`;
  document.querySelector("#result-count").textContent = `${filtered.length} package${filtered.length === 1 ? "" : "s"}`;
  packageGrid.innerHTML = filtered.map((pkg) => {
    const inventory = [...pkg.agents.map((item) => `agent: ${item}`), ...pkg.skills.map((item) => `skill: ${item}`)];
    return `<article class="package"><div class="package-top"><h3>${escapeHtml(pkg.displayName)}</h3><span class="badge ${pkg.classification === "internal" ? "internal" : ""}">${pkg.classification}</span></div><p>${escapeHtml(pkg.description)}</p><div class="inventory">${inventory.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("")}</div><a class="install" href="https://microsoft.github.io/apm/consumer/install-packages/" title="Open APM install documentation">$ ${escapeHtml(pkg.install)}</a></article>`;
  }).join("");
  empty.hidden = filtered.length !== 0;
}

function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[char])); }

fetch("catalog.json").then((response) => response.json()).then((catalog) => {
  state.packages = catalog.packages;
  ownerFilter.innerHTML = catalog.owners.map((owner) => `<option value="${escapeHtml(owner)}">${escapeHtml(owner[0].toUpperCase() + owner.slice(1))}</option>`).join("");
  ownerFilter.value = state.owner;
  document.querySelector("#updated").textContent = catalog.generatedAt
    ? `Updated ${new Date(catalog.generatedAt).toLocaleDateString()}`
    : "Latest marketplace metadata";
  render();
}).catch(() => { document.querySelector("#updated").textContent = "Catalogue unavailable"; });

ownerFilter.addEventListener("change", (event) => { state.owner = event.target.value; render(); });
search.addEventListener("input", (event) => { state.query = event.target.value; render(); });
