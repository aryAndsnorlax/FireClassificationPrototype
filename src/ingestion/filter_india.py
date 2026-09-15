"""
Filter NASA FIRMS hotspots to points that fall inside India's boundary.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.utils.config import DATA_RAW, DATA_INTERIM


# Input: historical FIRMS data covering the India-region bounding box
FIRMS_FILE = DATA_RAW / "firms" / "firms_history.csv"

# Actual India boundary
INDIA_BOUNDARY_FILE = DATA_RAW / "boundaries" / "india_boundary.geojson"

# Output: only FIRMS hotspots that fall inside India
OUTPUT_FILE = DATA_INTERIM / "firms_history_india.csv"


def filter_firms_to_india():
    # Load historical FIRMS hotspot data
    df = pd.read_csv(FIRMS_FILE)

    print(f"Loaded FIRMS hotspots: {len(df)}")

    # Create geographic points from longitude/latitude
    geometry = [
        Point(lon, lat)
        for lon, lat in zip(df["longitude"], df["latitude"])
    ]

    firms = gpd.GeoDataFrame(
        df,
        geometry=geometry,
        crs="EPSG:4326",
    )

    # Load India's actual boundary
    india = gpd.read_file(INDIA_BOUNDARY_FILE).to_crs("EPSG:4326")

    # Keep only hotspots that fall inside India's boundary
    firms_india = gpd.sjoin(
        firms,
        india[["geometry"]],
        how="inner",
        predicate="within",
    )

    # Remove GeoPandas-specific columns
    firms_india = firms_india.drop(
        columns=["geometry", "index_right"],
        errors="ignore",
    )

    # Save India-only historical FIRMS data
    firms_india.to_csv(OUTPUT_FILE, index=False)

    print()
    print("========== INDIA FILTER RESULT ==========")
    print(f"Original FIRMS hotspots : {len(df)}")
    print(f"India-only hotspots     : {len(firms_india)}")
    print(f"Removed outside India   : {len(df) - len(firms_india)}")
    print(f"Saved to                : {OUTPUT_FILE}")
    print("==========================================")


if __name__ == "__main__":
    filter_firms_to_india()