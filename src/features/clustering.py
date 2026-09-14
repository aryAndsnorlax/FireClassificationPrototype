"""DBSCAN features for simultaneous spatially-close FIRMS hotspots."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0088


def _cluster_one_day(day: pd.DataFrame, eps_km: float, min_samples: int) -> pd.DataFrame:
    result = day.copy()
    coords = np.radians(result[["latitude", "longitude"]].to_numpy(dtype=float))
    eps_rad = eps_km / EARTH_RADIUS_KM
    labels = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine").fit_predict(coords)
    result["cluster_id"] = labels
    sizes = pd.Series(labels).value_counts().to_dict()
    result["cluster_size"] = [1 if label == -1 else sizes[label] for label in labels]
    return result


def add_cluster_features(
    df: pd.DataFrame,
    eps_km: float = 1.0,
    min_samples: int = 2,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> pd.DataFrame:
    """Run DBSCAN independently per acquisition date.

    Clustering across different dates would incorrectly make persistent
    sources look like one large spatial event, so date is an explicit boundary.
    """
    required = {lat_col, lon_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing clustering columns: {sorted(missing)}")

    result = df.copy()
    # Unit-test/interactive callers may omit a date. In that case all rows are
    # treated as one observation window; the production pipeline always passes
    # FIRMS acq_date, so clustering remains date-specific there.
    if "acq_date" not in result.columns:
        result["acq_date"] = pd.Timestamp("1970-01-01")
    else:
        result["acq_date"] = pd.to_datetime(result["acq_date"], errors="coerce")
    result["_row_order"] = np.arange(len(result))
    parts = []
    for _, day in result.groupby(result["acq_date"].dt.normalize(), dropna=False, sort=False):
        valid = day[lat_col].notna() & day[lon_col].notna()
        if valid.sum() == 0:
            day = day.copy()
            day["cluster_id"] = -1
            day["cluster_size"] = 1
            parts.append(day)
            continue
        clustered = _cluster_one_day(day.loc[valid], eps_km, min_samples)
        invalid = day.loc[~valid].copy()
        invalid["cluster_id"] = -1
        invalid["cluster_size"] = 1
        parts.extend([clustered, invalid])

    result = pd.concat(parts, ignore_index=True).sort_values("_row_order")
    return result.drop(columns=["_row_order"]).reset_index(drop=True)


if __name__ == "__main__":
    from src.utils.config import DATA_INTERIM
    input_path = DATA_INTERIM / "hotspots_with_temporal_features.csv"
    output_path = DATA_INTERIM / "hotspots_with_cluster_features.csv"
    result = add_cluster_features(pd.read_csv(input_path))
    result.to_csv(output_path, index=False)
    print(f"Saved {len(result)} hotspots to {output_path}")
