"""
Pull industrial infrastructure polygons/points for India from OpenStreetMap
via the Overpass API.

Tags of interest: landuse=industrial, power=plant, man_made=works,
industrial=oil, industrial=refinery, landuse=quarry, etc.
"""
import requests
import geopandas as gpd
from shapely.geometry import shape

from src.utils.config import DATA_RAW, INDIA_BBOX

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# (min_lat, min_lon, max_lat, max_lon) — Overpass wants lat/lon order, not lon/lat
_min_lon, _min_lat, _max_lon, _max_lat = INDIA_BBOX
OVERPASS_BBOX = f"{_min_lat},{_min_lon},{_max_lat},{_max_lon}"

QUERY_TEMPLATE = """
[out:json][timeout:180];
(
  way["landuse"="industrial"]({bbox});
  way["power"="plant"]({bbox});
  way["man_made"="works"]({bbox});
  way["industrial"]({bbox});
  way["landuse"="quarry"]({bbox});
  node["power"="plant"]({bbox});
);
out geom;
"""


def fetch_osm_industrial(bbox: str = OVERPASS_BBOX) -> gpd.GeoDataFrame:
    """Query Overpass for industrial-related features within the bbox."""
    query = QUERY_TEMPLATE.format(bbox=bbox)
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=200)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    records = []
    for el in elements:
        if el["type"] == "node":
            geom = shape({"type": "Point", "coordinates": [el["lon"], el["lat"]]})
        elif el["type"] == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            geom = shape({"type": "LineString", "coordinates": coords})
        else:
            continue
        records.append({
            "osm_id": el["id"],
            "tags": el.get("tags", {}),
            "facility_type": el.get("tags", {}).get(
                "industrial", el.get("tags", {}).get("power", "unspecified")
            ),
            "geometry": geom,
        })

    return gpd.GeoDataFrame(records, crs="EPSG:4326")


if __name__ == "__main__":
    gdf = fetch_osm_industrial()
    out_path = DATA_RAW / "osm" / "osm_industrial_india.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    print(f"Saved {len(gdf)} industrial features to {out_path}")
