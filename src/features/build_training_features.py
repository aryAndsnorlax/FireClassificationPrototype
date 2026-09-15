"""
Build historical training features for FIRMS fire classification.

Training flow:
    India-only FIRMS history
        -> land cover
        -> OSM spatial features
        -> historical temporal features
        -> same-day clustering
        -> training dataset

This module is separate from temporal_features.py because training
features must avoid using future observations for each training sample.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.config import DATA_INTERIM, DATA_RAW


# ---------------------------------------------------------------------
# Input / output files
# ---------------------------------------------------------------------

FIRMS_FILE = DATA_INTERIM / "firms_history_india.csv"

LANDCOVER_FILE = DATA_INTERIM / "training_hotspots_with_landcover.csv"

SPATIAL_FILE = DATA_INTERIM / "training_hotspots_with_spatial_features.csv"

TEMPORAL_FILE = DATA_INTERIM / "training_hotspots_with_temporal_features.csv"

CLUSTER_FILE = DATA_INTERIM / "training_hotspots_with_cluster_features.csv"


# ---------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------

def assign_grid_id(df: pd.DataFrame, grid_size: float = 0.01) -> pd.DataFrame:
    """
    Assign each hotspot to an approximately 1 km spatial grid.
    """

    result = df.copy()

    result["grid_id"] = (
        np.floor(result["latitude"] / grid_size).astype("Int64").astype(str)
        + "_"
        + np.floor(result["longitude"] / grid_size).astype("Int64").astype(str)
    )

    return result


# ---------------------------------------------------------------------
# Temporal features
# ---------------------------------------------------------------------

def build_past_only_temporal_features(
    current: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build temporal features using only observations available before
    each hotspot's acquisition date.

    This prevents future observations from leaking into training features.
    """

    current = current.copy()
    history = history.copy()

    current["acq_date"] = pd.to_datetime(
        current["acq_date"],
        errors="coerce",
    )

    history["acq_date"] = pd.to_datetime(
        history["acq_date"],
        errors="coerce",
    )

    current = assign_grid_id(current)
    history = assign_grid_id(history)

    # Ensure chronological processing
    current = current.sort_values("acq_date").reset_index(drop=True)
    history = history.sort_values("acq_date").reset_index(drop=True)

    persistence_count = []
    active_days = []
    mean_frp = []
    median_frp = []
    max_frp = []

    for _, row in current.iterrows():

        date = row["acq_date"]
        grid = row["grid_id"]

        previous = history[
            (history["grid_id"] == grid)
            & (history["acq_date"] < date)
        ]

        if previous.empty:
            persistence_count.append(0)
            active_days.append(0)
            mean_frp.append(0.0)
            median_frp.append(0.0)
            max_frp.append(0.0)
            continue

        persistence_count.append(len(previous))

        active_days.append(
            previous["acq_date"]
            .dt.normalize()
            .nunique()
        )

        frp_values = pd.to_numeric(
            previous.get("frp"),
            errors="coerce",
        ).dropna()

        if frp_values.empty:
            mean_frp.append(0.0)
            median_frp.append(0.0)
            max_frp.append(0.0)
        else:
            mean_frp.append(float(frp_values.mean()))
            median_frp.append(float(frp_values.median()))
            max_frp.append(float(frp_values.max()))

    current["persistence_count"] = persistence_count
    current["active_days"] = active_days
    current["mean_frp"] = mean_frp
    current["median_frp"] = median_frp
    current["max_frp"] = max_frp

    # Calculate persistence relative to the number of days that
    # have actually elapsed before the current observation.
    first_date = history["acq_date"].min()

    elapsed_days = (
        current["acq_date"] - first_date
    ).dt.days.clip(lower=1)

    current["persistence_score"] = (
        current["active_days"] / elapsed_days
    ).clip(0.0, 1.0)

    current["frp"] = pd.to_numeric(
        current.get("frp"),
        errors="coerce",
    )

    current["frp_baseline"] = current["median_frp"]

    current["frp_deviation"] = (
        current["frp"] - current["frp_baseline"]
    )

    current["frp_ratio_to_baseline"] = np.where(
        current["frp_baseline"] > 0,
        current["frp"] / current["frp_baseline"],
        0.0,
    )

    current["frp_ratio_to_baseline"] = (
        current["frp_ratio_to_baseline"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )

    return current


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def build_training_features() -> pd.DataFrame:
    """
    Build the initial historical training feature dataset.

    The spatial and land-cover stages are intentionally kept separate
    so that the existing project modules can be reused.
    """

    if not FIRMS_FILE.exists():
        raise FileNotFoundError(
            f"India-only FIRMS file not found: {FIRMS_FILE}"
        )

    df = pd.read_csv(FIRMS_FILE)

    required_columns = [
        "latitude",
        "longitude",
        "acq_date",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    print("==========================================")
    print("BUILDING HISTORICAL TRAINING FEATURES")
    print("==========================================")
    print(f"Input rows: {len(df)}")

    df["acq_date"] = pd.to_datetime(
        df["acq_date"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "latitude",
            "longitude",
            "acq_date",
        ]
    ).reset_index(drop=True)

    # Assign stable spatial grid.
    df = assign_grid_id(df)

    print(f"Valid training rows: {len(df)}")
    print(f"Unique dates: {df['acq_date'].dt.date.nunique()}")
    print(f"Unique spatial grids: {df['grid_id'].nunique()}")

    # Build past-only temporal features.
    df = build_past_only_temporal_features(
        current=df,
        history=df,
    )

    Path(TEMPORAL_FILE).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        TEMPORAL_FILE,
        index=False,
    )

    print()
    print("Temporal features created.")
    print(f"Rows: {len(df)}")
    print(f"Saved to: {TEMPORAL_FILE}")

    return df


if __name__ == "__main__":
    build_training_features()