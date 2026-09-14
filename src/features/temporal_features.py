import pandas as pd
import numpy as np

from src.utils.config import DATA_RAW, DATA_INTERIM


HISTORY_FILE = DATA_RAW / "firms" / "firms_history_10days.csv"
CURRENT_FILE = DATA_INTERIM / "hotspots_features.csv"
OUTPUT_FILE = DATA_INTERIM / "hotspots_with_temporal_features.csv"


# Approximately 1 km grid.
# Latitude: 1 degree ≈ 111 km.
# Longitude is adjusted using latitude.
GRID_SIZE_DEGREES = 0.01


def create_grid_id(latitude, longitude):
    """
    Assign a FIRMS detection to an approximately 1 km spatial grid.

    Using a grid allows us to identify repeated fire activity
    even when satellite detections do not have exactly the
    same latitude/longitude.
    """

    lat_grid = np.floor(latitude / GRID_SIZE_DEGREES)
    lon_grid = np.floor(longitude / GRID_SIZE_DEGREES)

    return f"{int(lat_grid)}_{int(lon_grid)}"


def build_temporal_features():
    print("Loading FIRMS history...")

    history = pd.read_csv(HISTORY_FILE)

    print(f"Historical records: {len(history)}")

    # Convert date to datetime
    history["acq_date"] = pd.to_datetime(
        history["acq_date"]
    )

    # Create spatial grid
    history["grid_id"] = history.apply(
        lambda row: create_grid_id(
            row["latitude"],
            row["longitude"]
        ),
        axis=1,
    )

    # --------------------------------------------------
    # Aggregate temporal activity by grid cell
    # --------------------------------------------------

    temporal = (
        history
        .groupby("grid_id")
        .agg(
            persistence_count=(
                "grid_id",
                "size"
            ),

            active_days=(
                "acq_date",
                "nunique"
            ),

            mean_frp=(
                "frp",
                "mean"
            ),

            max_frp=(
                "frp",
                "max"
            ),

            mean_brightness=(
                "brightness",
                "mean"
            ),

            max_brightness=(
                "brightness",
                "max"
            ),
        )
        .reset_index()
    )

    print()
    print(f"Unique active grid cells: {len(temporal)}")

    # --------------------------------------------------
    # Load current 43-hotspot dataset
    # --------------------------------------------------

    current = pd.read_csv(CURRENT_FILE)

    print(f"Current hotspots: {len(current)}")

    # Create the same grid ID
    current["grid_id"] = current.apply(
        lambda row: create_grid_id(
            row["latitude"],
            row["longitude"]
        ),
        axis=1,
    )

    # --------------------------------------------------
    # Merge temporal information
    # --------------------------------------------------

    result = current.merge(
        temporal,
        on="grid_id",
        how="left",
    )

    # --------------------------------------------------
    # Handle hotspots with no matching history
    # --------------------------------------------------

    temporal_columns = [
        "persistence_count",
        "active_days",
        "mean_frp",
        "max_frp",
        "mean_brightness",
        "max_brightness",
    ]

    for column in temporal_columns:
        result[column] = result[column].fillna(0)

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("Temporal feature summary:")
    print(
        result[
            [
                "persistence_count",
                "active_days",
                "mean_frp",
                "max_frp",
            ]
        ].describe()
    )

    print()
    print(f"Final rows: {len(result)}")
    print(f"Final columns: {len(result.columns)}")

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_temporal_features()