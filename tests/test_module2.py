import pandas as pd

from src.labeling.rule_based_labels import classify_hotspot


def test_official_label_rules():
    base = dict(distance_to_facility_m=5000, persistence_score=0.1, frp_ratio_to_baseline=1.0)
    assert classify_hotspot(pd.Series({**base, "landcover_class": "cropland", "nearest_facility_type": ""})) == "agricultural_burning"
    assert classify_hotspot(pd.Series({**base, "landcover_class": "tree_cover", "nearest_facility_type": ""})) == "wildfire"
    assert classify_hotspot(pd.Series({**base, "landcover_class": "built_up", "nearest_facility_type": ""})) == "unknown"
    assert classify_hotspot(pd.Series({**base, "landcover_class": "built_up", "nearest_facility_type": "mine", "distance_to_facility_m": 100})) == "coal_seam_fire"
    assert classify_hotspot(pd.Series({**base, "landcover_class": "built_up", "nearest_facility_type": "refinery", "distance_to_facility_m": 100, "frp_ratio_to_baseline": 5.0})) == "industrial_fire"
    assert classify_hotspot(pd.Series({**base, "landcover_class": "built_up", "nearest_facility_type": "refinery", "distance_to_facility_m": 100, "persistence_score": 0.8})) == "persistent_industrial"
