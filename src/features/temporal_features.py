"""
Temporal feature engineering: for each hotspot location, compute
- detection frequency over a trailing window (persistence score)
- FRP baseline (mean/std) and how far the current detection deviates from it
"""
import pandas as pd
import numpy as np

from src.utils.config import DATA_INTERIM, PERSISTENCE_FREQ_THRESHOLD

# Grid resolution (degrees) used to bucket nearby detections into the same
# "location" for persistence/baseline calculations. ~0.01 deg ~ 1km.
GRID_SIZE = 0.01


def assign_grid_cell(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["grid_lat"] = (df["latitude"] / GRID_SIZE).round().astype(int)
    df["grid_lon"] = (df["longitude"] / GRID_SIZE).round().astype(int)
    df["grid_id"] = df["grid_lat"].astype(str) + "_" + df["grid_lon"].astype(str)
    return df


def compute_persistence(df: pd.DataFrame, date_col: str = "acq_date",
                         window_days: int = 90) -> pd.DataFrame:
    """
    For each grid cell, compute the fraction of days within the trailing
    window that had at least one detection — this is the persistence score
    used to separate flares/kilns (high, steady) from one-off events (low).
    """
    df = assign_grid_cell(df)
    df[date_col] = pd.to_datetime(df[date_col])

    counts = df.groupby("grid_id")[date_col].nunique().rename("days_detected")
    df = df.merge(counts, on="grid_id", how="left")
    df["persistence_score"] = (df["days_detected"] / window_days).clip(upper=1.0)
    df["is_persistent"] = df["persistence_score"] >= PERSISTENCE_FREQ_THRESHOLD
    return df


def compute_frp_baseline(df: pd.DataFrame, frp_col: str = "frp") -> pd.DataFrame:
    """
    For each grid cell, compute the historical mean/std of FRP and the
    z-score / ratio of each detection relative to its own location's baseline.
    A high ratio at a known industrial site is the strongest single signal
    for "possible accident" rather than normal operation.
    """
    df = assign_grid_cell(df) if "grid_id" not in df.columns else df
    stats = df.groupby("grid_id")[frp_col].agg(["mean", "std"]).rename(
        columns={"mean": "frp_baseline_mean", "std": "frp_baseline_std"}
    )
    df = df.merge(stats, on="grid_id", how="left")
    df["frp_baseline_std"] = df["frp_baseline_std"].fillna(0)
    df["frp_ratio_to_baseline"] = df[frp_col] / df["frp_baseline_mean"].replace(0, np.nan)
    df["frp_ratio_to_baseline"] = df["frp_ratio_to_baseline"].fillna(1.0)
    return df


def run(input_path: str) -> pd.DataFrame:
    df = pd.read_csv(input_path) if input_path.endswith(".csv") else pd.read_json(input_path)
    df = compute_persistence(df)
    df = compute_frp_baseline(df)
    return df


if __name__ == "__main__":
    input_path = DATA_INTERIM / "hotspots_with_spatial_features.geojson"
    df = run(str(input_path))
    out_path = DATA_INTERIM / "hotspots_with_temporal_features.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} hotspots with temporal features to {out_path}")
