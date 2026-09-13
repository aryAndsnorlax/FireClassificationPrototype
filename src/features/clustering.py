"""
Spatial clustering of simultaneous/nearby hotspots using DBSCAN.
Large, spread-out clusters are characteristic of wildfires; single or
small clusters are more typical of industrial sources and agri-burning.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0


def add_cluster_features(df: pd.DataFrame, eps_km: float = 1.0, min_samples: int = 2,
                          lat_col: str = "latitude", lon_col: str = "longitude") -> pd.DataFrame:
    """
    Cluster same-day hotspots that are spatially close together (haversine
    distance) and attach a cluster_id + cluster_size to each row.
    """
    df = df.copy()
    coords = np.radians(df[[lat_col, lon_col]].to_numpy())
    eps_rad = eps_km / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine")
    df["cluster_id"] = db.fit_predict(coords)

    cluster_sizes = df.groupby("cluster_id").size().rename("cluster_size")
    df = df.merge(cluster_sizes, on="cluster_id", how="left")
    # noise points (cluster_id == -1) are isolated single detections
    df.loc[df["cluster_id"] == -1, "cluster_size"] = 1
    return df


if __name__ == "__main__":
    from src.utils.config import DATA_INTERIM

    input_path = DATA_INTERIM / "hotspots_with_temporal_features.csv"
    df = pd.read_csv(input_path)
    df = add_cluster_features(df)
    out_path = DATA_INTERIM / "hotspots_with_cluster_features.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} hotspots with cluster features to {out_path}")
