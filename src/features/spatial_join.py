"""
Spatial feature engineering for FIRMS hotspots.

For each hotspot, calculate:
- distance to nearest industrial facility
- nearest facility type
- distance to selected facility categories
"""

import geopandas as gpd
import pandas as pd

from src.utils.geo_utils import df_to_geodataframe, nearest_distance
from src.utils.config import DATA_RAW, DATA_INTERIM


FACILITY_TYPES = [
    "industrial",
    "plant",
    "quarry",
    "works",
    "factory",
    "mine",
    "refinery",
    "brickyard",
]


def add_facility_distance(
    hotspots: gpd.GeoDataFrame,
    facilities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Add nearest facility distance and type."""

    hotspots = hotspots.reset_index(drop=True).copy()

    dist_df = nearest_distance(
        hotspots,
        facilities,
        target_id_col="facility_type",
    )

    hotspots["distance_to_facility_m"] = dist_df["distance_m"]
    hotspots["nearest_facility_type"] = dist_df["facility_type"]

    return hotspots


def add_category_distances(
    hotspots: gpd.GeoDataFrame,
    facilities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Add distance to the nearest facility for each selected category."""

    hotspots = hotspots.copy()

    for facility_type in FACILITY_TYPES:

        subset = facilities[
            facilities["facility_type"].str.lower() == facility_type
        ].copy()

        column_name = f"distance_to_{facility_type}_m"

        if subset.empty:
            hotspots[column_name] = float("nan")
            continue

        dist_df = nearest_distance(
            hotspots,
            subset,
            target_id_col="facility_type",
        )

        hotspots[column_name] = dist_df["distance_m"].values

    return hotspots


def run(
    firms_csv: str,
    osm_geojson: str,
) -> gpd.GeoDataFrame:

    # Load India-only FIRMS hotspots
    firms_df = pd.read_csv(firms_csv)

    hotspots = df_to_geodataframe(firms_df)

    # Load OSM facilities
    facilities = gpd.read_file(osm_geojson)

    # Make sure CRS matches
    facilities = facilities.to_crs("EPSG:4326")

    # Overall nearest facility
    hotspots = add_facility_distance(
        hotspots,
        facilities,
    )

    # Nearest facility by category
    hotspots = add_category_distances(
        hotspots,
        facilities,
    )

    return hotspots


if __name__ == "__main__":

    result = run(
        firms_csv=str(
            DATA_INTERIM / "firms_india.csv"
        ),
        osm_geojson=str(
            DATA_RAW
            / "osm"
            / "osm_industrial_india.geojson"
        ),
    )

    out_path = (
        DATA_INTERIM
        / "hotspots_with_spatial_features.geojson"
    )

    result.to_file(
        out_path,
        driver="GeoJSON",
    )

    print()
    print(f"Processed hotspots: {len(result)}")
    print(f"Features created: {len(result.columns)}")
    print(f"Saved to: {out_path}")