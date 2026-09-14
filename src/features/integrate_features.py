import pandas as pd
import geopandas as gpd

from src.utils.config import DATA_INTERIM


LANDCOVER_FILE = DATA_INTERIM / "hotspots_with_landcover.csv"
SPATIAL_FILE = DATA_INTERIM / "hotspots_with_spatial_features.geojson"
OUTPUT_FILE = DATA_INTERIM / "hotspots_features.csv"


def integrate_features():
    # Load land-cover features
    landcover = pd.read_csv(LANDCOVER_FILE)

    # Load OSM spatial features
    spatial = gpd.read_file(SPATIAL_FILE)

    # Remove geometry because this will be our tabular ML dataset
    spatial = spatial.drop(columns=["geometry"], errors="ignore")

    # Columns identifying the same FIRMS hotspot
    key_columns = [
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
        "satellite",
        "sensor",
    ]

    # Make date fields consistent
    spatial["acq_date"] = pd.to_datetime(
        spatial["acq_date"]
    ).dt.strftime("%Y-%m-%d")

    landcover["acq_date"] = pd.to_datetime(
        landcover["acq_date"]
    ).dt.strftime("%Y-%m-%d")

    # Make time fields consistent
    spatial["acq_time"] = spatial["acq_time"].astype(str)
    landcover["acq_time"] = landcover["acq_time"].astype(str)

    # Select land-cover columns
    landcover_columns = key_columns + [
        "worldcover_value",
        "landcover_class",
        "worldcover_tile",
    ]

    landcover = landcover[landcover_columns]

    # Merge spatial and land-cover features
    merged = spatial.merge(
        landcover,
        on=key_columns,
        how="left",
    )

    # Save final feature dataset
    merged.to_csv(OUTPUT_FILE, index=False)

    print()
    print(f"Spatial hotspots: {len(spatial)}")
    print(f"Land-cover hotspots: {len(landcover)}")
    print(f"Final feature rows: {len(merged)}")
    print(f"Final feature columns: {len(merged.columns)}")

    print()
    print("Land-cover distribution:")
    print(
        merged["landcover_class"].value_counts(
            dropna=False
        )
    )

    print()
    print("Feature columns:")

    for column in merged.columns:
        print(f"  - {column}")

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    integrate_features()