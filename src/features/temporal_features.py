"""Temporal feature engineering for FIRMS hotspots.

The module is deliberately reusable: tests and downstream code can call
``assign_grid_cell`` and ``compute_persistence`` directly, while the CLI
builds the project's temporal feature CSV.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.config import DATA_RAW, DATA_INTERIM

HISTORY_FILE = DATA_RAW / "firms" / "firms_history.csv"
CURRENT_FILE = DATA_INTERIM / "hotspots_with_spatial_features.csv"
OUTPUT_FILE = DATA_INTERIM / "hotspots_with_temporal_features.csv"

GRID_SIZE_DEGREES = 0.01  # approximately 1 km at Indian latitudes


def create_grid_id(latitude: float, longitude: float) -> str:
    """Return a stable ~1 km grid identifier from latitude/longitude."""
    if pd.isna(latitude) or pd.isna(longitude):
        return "unknown"
    return f"{int(np.floor(float(latitude) / GRID_SIZE_DEGREES))}_{int(np.floor(float(longitude) / GRID_SIZE_DEGREES))}"


def assign_grid_cell(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``grid_id`` to a dataframe containing latitude/longitude."""
    result = df.copy()
    result["grid_id"] = [
        create_grid_id(lat, lon)
        for lat, lon in zip(result["latitude"], result["longitude"])
    ]
    return result


def compute_persistence(df: pd.DataFrame, window_days: int = 90) -> pd.DataFrame:
    """Compute persistence metrics for each hotspot's spatial grid.

    ``persistence_score`` is the fraction of the requested time window on
    which the grid was detected, bounded to [0, 1].  If a dataframe contains
    fewer than ``window_days`` distinct days, the denominator is the observed
    span (at least one day), preventing artificially tiny scores in short
    samples.
    """
    if window_days <= 0:
        raise ValueError("window_days must be positive")

    result = assign_grid_cell(df)
    result["acq_date"] = pd.to_datetime(result["acq_date"], errors="coerce")
    if result["acq_date"].isna().all():
        result["active_days"] = 0
        result["persistence_count"] = 0
        result["persistence_score"] = 0.0
        return result

    observed_days = int(result["acq_date"].dt.normalize().nunique())
    denominator = max(1, min(window_days, observed_days))

    stats = (
        result.dropna(subset=["acq_date"])
        .groupby("grid_id")
        .agg(
            persistence_count=("grid_id", "size"),
            active_days=("acq_date", lambda s: s.dt.normalize().nunique()),
        )
        .reset_index()
    )
    stats["persistence_score"] = (
        stats["active_days"] / float(denominator)
    ).clip(0.0, 1.0)

    return result.drop(columns=["persistence_count", "active_days", "persistence_score"], errors="ignore").merge(
        stats, on="grid_id", how="left"
    )


def _frp_stats(history: pd.DataFrame) -> pd.DataFrame:
    history = assign_grid_cell(history)
    history["frp"] = pd.to_numeric(history.get("frp"), errors="coerce")
    history = history.dropna(subset=["frp"])
    if history.empty:
        return pd.DataFrame(columns=["grid_id", "mean_frp", "median_frp", "max_frp", "frp_baseline"])

    stats = history.groupby("grid_id").agg(
        mean_frp=("frp", "mean"),
        median_frp=("frp", "median"),
        max_frp=("frp", "max"),
        frp_baseline=("frp", "median"),
    ).reset_index()
    return stats


def build_temporal_features(
    history_file: str | Path = HISTORY_FILE,
    current_file: str | Path = CURRENT_FILE,
    output_file: str | Path = OUTPUT_FILE,
) -> pd.DataFrame:
    """Build persistence and FRP-baseline/deviation features."""
    history = pd.read_csv(history_file)
    current = pd.read_csv(current_file)

    history["acq_date"] = pd.to_datetime(history["acq_date"], errors="coerce")
    current["acq_date"] = pd.to_datetime(current["acq_date"], errors="coerce")

    current = compute_persistence(current, window_days=max(1, history["acq_date"].dt.normalize().nunique()))

    history = assign_grid_cell(history)
    temporal = (
        history.groupby("grid_id")
        .agg(
            persistence_count=("grid_id", "size"),
            active_days=("acq_date", lambda s: s.dt.normalize().nunique()),
            mean_frp=("frp", "mean"),
            median_frp=("frp", "median"),
            max_frp=("frp", "max"),
            mean_brightness=("brightness", "mean") if "brightness" in history else ("grid_id", "size"),
            max_brightness=("brightness", "max") if "brightness" in history else ("grid_id", "size"),
        )
        .reset_index()
    )
    # If brightness was unavailable, the temporary size-based values above are
    # removed rather than pretending they are brightness measurements.
    if "brightness" not in history:
        temporal = temporal.drop(columns=["mean_brightness", "max_brightness"], errors="ignore")

    temporal["frp_baseline"] = temporal["median_frp"]
    current = current.merge(temporal, on="grid_id", how="left", suffixes=("", "_history"))

    # Prefer the history-derived persistence/FRP statistics.
    for col in ["persistence_count", "active_days", "mean_frp", "median_frp", "max_frp", "frp_baseline", "mean_brightness", "max_brightness"]:
        history_col = f"{col}_history"
        if history_col in current:
            current[col] = current[history_col]
            current.drop(columns=[history_col], inplace=True)

    current["persistence_count"] = current["persistence_count"].fillna(0)
    current["active_days"] = current["active_days"].fillna(0)
    current["persistence_score"] = (
        current["active_days"] / max(1, history["acq_date"].dt.normalize().nunique())
    ).clip(0.0, 1.0)

    for col in ["mean_frp", "median_frp", "max_frp", "frp_baseline", "mean_brightness", "max_brightness"]:
        if col in current:
            current[col] = pd.to_numeric(current[col], errors="coerce")

    current["frp"] = pd.to_numeric(current.get("frp"), errors="coerce")
    current["frp_deviation"] = current["frp"] - current["frp_baseline"]
    current["frp_ratio_to_baseline"] = np.where(
        current["frp_baseline"].gt(0),
        current["frp"] / current["frp_baseline"],
        0.0,
    )
    current["frp_ratio_to_baseline"] = current["frp_ratio_to_baseline"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    current.to_csv(output_file, index=False)
    return current


if __name__ == "__main__":
    result = build_temporal_features()
    print(f"Saved {len(result)} rows to {OUTPUT_FILE}")
