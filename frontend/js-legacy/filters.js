// Renders class/date filter controls and re-queries the map layer on change.

const FIRE_CLASSES = [
  "industrial_fire",
  "persistent_industrial",
  "coal_seam_fire",
  "agricultural_burning",
  "wildfire",
  "unknown",
];

function renderFilters() {
  const container = document.getElementById("filters");

  const select = document.createElement("select");
  select.innerHTML =
    `<option value="">All classes</option>` +
    FIRE_CLASSES.map((c) => `<option value="${c}">${c}</option>`).join("");

  select.addEventListener("change", () => {
    const filters = select.value ? { class: select.value } : {};
    loadHotspots(filters); // defined in map.js, loaded first
  });

  container.appendChild(select);
}

renderFilters();
