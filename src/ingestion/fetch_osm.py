"""
Pull industrial infrastructure from OpenStreetMap using Overpass.

The India bounding box is divided into smaller regions so that
Overpass requests remain manageable.
"""

import requests
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

from src.utils.config import DATA_RAW


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# Smaller regions instead of querying the whole India bounding box at once.
# Format: (name, min_lon, min_lat, max_lon, max_lat)
REGIONS = [
    ("north", 68, 20, 80, 37),
    ("central", 76, 15, 88, 25),
    ("east", 84, 20, 97, 29),
    ("south", 74, 6, 86, 20),
]


QUERY_TEMPLATE = """
[out:json][timeout:120];
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


def build_bbox(min_lon, min_lat, max_lon, max_lat):
    """Build Overpass bbox in south,west,north,east order."""
    return f"{min_lat},{min_lon},{max_lat},{max_lon}"


def fetch_region(name, min_lon, min_lat, max_lon, max_lat):
    """Fetch OSM industrial features for one region."""

    bbox = build_bbox(min_lon, min_lat, max_lon, max_lat)
    query = QUERY_TEMPLATE.format(bbox=bbox)

    headers = {
        "User-Agent": "FireClassificationPrototype/1.0"
    }

    print(f"Fetching OSM region: {name}")

    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers=headers,
        timeout=180,
    )

    response.raise_for_status()

    elements = response.json().get("elements", [])

    records = []

    for el in elements:

        tags = el.get("tags", {})

        if el["type"] == "node":

            geom = Point(
                el["lon"],
                el["lat"]
            )

        elif el["type"] == "way" and "geometry" in el:

            coords = [
                (point["lon"], point["lat"])
                for point in el["geometry"]
            ]

            # Closed ways can represent areas/polygons.
            if len(coords) >= 4 and coords[0] == coords[-1]:
                try:
                    geom = Polygon(coords)

                    if not geom.is_valid:
                        geom = geom.buffer(0)

                except Exception:
                    geom = LineString(coords)

            else:
                geom = LineString(coords)

        else:
            continue

        records.append({
            "osm_id": el["id"],
            "osm_type": el["type"],
            "name": tags.get("name"),
            "facility_type": (
                tags.get("industrial")
                or tags.get("power")
                or tags.get("landuse")
                or tags.get("man_made")
                or "unspecified"
            ),
            "geometry": geom,
        })

    print(f"  Found {len(records)} features")

    return records


def fetch_osm_industrial():
    """Fetch industrial infrastructure across the configured regions."""

    all_records = []

    for region in REGIONS:
        name, min_lon, min_lat, max_lon, max_lat = region

        try:
            records = fetch_region(
                name,
                min_lon,
                min_lat,
                max_lon,
                max_lat,
            )

            all_records.extend(records)

        except requests.RequestException as error:
            print(f"  WARNING: region '{name}' failed: {error}")

    gdf = gpd.GeoDataFrame(
        all_records,
        geometry="geometry",
        crs="EPSG:4326",
    )

    return gdf


if __name__ == "__main__":

    gdf = fetch_osm_industrial()

    out_path = (
        DATA_RAW
        / "osm"
        / "osm_industrial_india.geojson"
    )

    gdf.to_file(
        out_path,
        driver="GeoJSON"
    )

    print()
    print(f"Total OSM features: {len(gdf)}")
    print(f"Saved to: {out_path}")