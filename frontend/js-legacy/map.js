// Initializes the Leaflet map centered on India and loads classified hotspots
// from the FastAPI backend as a GeoJSON layer, color-coded by class.

const API_BASE = "http://localhost:8000";

const CLASS_COLORS = {
  industrial_fire: "#e63946",        // red — highest priority
  persistent_industrial: "#f4a261",  // orange
  coal_seam_fire: "#8d5524",         // brown
  agricultural_burning: "#e9c46a",   // yellow
  wildfire: "#2a9d8f",               // teal
  unknown: "#a8a8a8",                // grey
};

const map = L.map("map").setView([22.5, 80.0], 5); // centered on India

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let hotspotLayer;

async function loadHotspots(filters = {}) {
  const params = new URLSearchParams(filters);
  const resp = await fetch(`${API_BASE}/hotspots/?${params.toString()}`);
  const geojson = await resp.json();

  if (hotspotLayer) map.removeLayer(hotspotLayer);

  hotspotLayer = L.geoJSON(geojson, {
    pointToLayer: (feature, latlng) =>
      L.circleMarker(latlng, {
        radius: 5,
        fillColor: CLASS_COLORS[feature.properties.class] || CLASS_COLORS.unknown,
        color: "#000",
        weight: 0.5,
        fillOpacity: 0.8,
      }),
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      layer.bindPopup(
        `<b>${p.class}</b><br/>FRP: ${p.frp ?? "n/a"}<br/>` +
        `Facility: ${p.facility_type ?? "n/a"}<br/>Date: ${p.acq_date ?? "n/a"}`
      );
    },
  }).addTo(map);
}

// initial load, no filters
loadHotspots();
