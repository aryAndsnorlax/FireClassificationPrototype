import pandas as pd

from src.features.clustering import add_cluster_features
from src.features.temporal_features import assign_grid_cell, compute_persistence


def test_assign_grid_cell_groups_nearby_points():
    df = pd.DataFrame({
        "latitude": [22.501, 22.502, 30.0],
        "longitude": [80.001, 80.002, 75.0],
    })
    result = assign_grid_cell(df)
    # first two points should land in the same grid cell, third should differ
    assert result.loc[0, "grid_id"] == result.loc[1, "grid_id"]
    assert result.loc[0, "grid_id"] != result.loc[2, "grid_id"]


def test_add_cluster_features_assigns_cluster_size():
    df = pd.DataFrame({
        "latitude": [22.50, 22.501, 30.0],
        "longitude": [80.00, 80.001, 75.0],
    })
    result = add_cluster_features(df, eps_km=1.0, min_samples=2)
    assert "cluster_size" in result.columns
    # the isolated third point should have cluster_size == 1
    assert result.loc[2, "cluster_size"] == 1


def test_compute_persistence_score_bounds():
    df = pd.DataFrame({
        "latitude": [22.5] * 5,
        "longitude": [80.0] * 5,
        "acq_date": pd.date_range("2026-01-01", periods=5),
    })
    result = compute_persistence(df, window_days=90)
    assert (result["persistence_score"] <= 1.0).all()
    assert (result["persistence_score"] >= 0.0).all()
