"""Weak, rule-based labels for the FIRMS fire-context classifier."""
from __future__ import annotations

import pandas as pd

from src.utils.config import DATA_INTERIM, DATA_PROCESSED, FIRE_CLASSES, FACILITY_PROXIMITY_M, PERSISTENCE_FREQ_THRESHOLD, FRP_ANOMALY_RATIO

INPUT_FILE = DATA_INTERIM / "hotspots_with_cluster_features.csv"
OUTPUT_FILE = DATA_PROCESSED / "labeled_hotspots.csv"

MIN_CONFIDENCE = 0.50

INDUSTRIAL_TYPES = {
    "industrial", "plant", "factory", "works", "refinery", "steelmaking",
    "metal_processing", "brickworks", "brickyard"
}
MINING_TYPES = {"quarry", "mine"}
VEGETATION_CLASSES = {"tree_cover", "shrubland", "grassland", "forest", "woodland"}


def _distance(row: pd.Series) -> float:
    value = pd.to_numeric(row.get("distance_to_facility_m"), errors="coerce")
    return float(value) if pd.notna(value) else float("inf")


def _ratio(row: pd.Series) -> float:
    value = pd.to_numeric(row.get("frp_ratio_to_baseline"), errors="coerce")
    return float(value) if pd.notna(value) else 0.0


def classify_hotspot(row: pd.Series) -> str:
    """Assign one of the six official project classes."""
    landcover = str(row.get("landcover_class", row.get("lc_class", ""))).strip().lower()
    facility = str(row.get("nearest_facility_type", "")).strip().lower()
    distance = _distance(row)
    persistence = pd.to_numeric(row.get("persistence_score"), errors="coerce")
    persistence = float(persistence) if pd.notna(persistence) else 0.0
    ratio = _ratio(row)

    near_facility = distance <= FACILITY_PROXIMITY_M
    near_mine = facility in MINING_TYPES or pd.to_numeric(row.get("distance_to_mine_m"), errors="coerce") <= FACILITY_PROXIMITY_M

    if near_mine:
        return "coal_seam_fire"

    if landcover == "cropland" and not near_facility:
        return "agricultural_burning"

    if landcover in VEGETATION_CLASSES and not near_facility:
        return "wildfire"

    if facility in INDUSTRIAL_TYPES and near_facility:
        if ratio >= FRP_ANOMALY_RATIO:
            return "industrial_fire"
        if persistence >= PERSISTENCE_FREQ_THRESHOLD:
            return "persistent_industrial"
        # A facility-adjacent hotspot without enough evidence of persistence
        # remains a possible industrial event rather than being forced into a
        # natural-fire class.
        return "industrial_fire"

    # Facility proximity can still be informative when the nearest type is
    # missing, so use the generic distance plus strong persistence/FRP evidence.
    if near_facility and (ratio >= FRP_ANOMALY_RATIO or persistence >= PERSISTENCE_FREQ_THRESHOLD):
        return "industrial_fire" if ratio >= FRP_ANOMALY_RATIO else "persistent_industrial"

    if landcover == "built_up" or landcover == "bare_sparse":
        return "unknown"

    return "unknown"


def calculate_label_confidence(row: pd.Series) -> float:
    """Return evidence strength for a weak label, not an ML probability."""
    label = row["fire_context"]
    landcover = str(row.get("landcover_class", row.get("lc_class", ""))).strip().lower()
    facility = str(row.get("nearest_facility_type", "")).strip().lower()
    distance = _distance(row)
    persistence_value = pd.to_numeric(row.get("persistence_score"), errors="coerce")
    persistence = float(persistence_value) if pd.notna(persistence_value) else 0.0
    ratio = _ratio(row)

    if label == "industrial_fire":
        score = 0.60
        if facility in INDUSTRIAL_TYPES and distance <= 500:
            score += 0.20
        if ratio >= FRP_ANOMALY_RATIO:
            score += 0.15
        return min(score, 0.98)
    if label == "persistent_industrial":
        score = 0.65
        if persistence >= PERSISTENCE_FREQ_THRESHOLD:
            score += 0.20
        if facility in INDUSTRIAL_TYPES:
            score += 0.10
        return min(score, 0.95)
    if label == "coal_seam_fire":
        return 0.90 if facility in MINING_TYPES else 0.75
    if label == "agricultural_burning":
        return 0.85 if landcover == "cropland" else 0.60
    if label == "wildfire":
        return 0.85 if landcover in VEGETATION_CLASSES else 0.60
    return 0.40


def create_labels(input_file=INPUT_FILE, output_file=OUTPUT_FILE) -> pd.DataFrame:
    df = pd.read_csv(input_file)
    if df.empty:
        raise ValueError("Cannot create labels from an empty feature dataset")

    df["fire_context"] = df.apply(classify_hotspot, axis=1)
    df["label_confidence"] = df.apply(calculate_label_confidence, axis=1).clip(0.0, 1.0)

    unknown_count = int((df["fire_context"] == "unknown").sum())
    if not set(df["fire_context"].unique()).issubset(set(FIRE_CLASSES)):
        raise RuntimeError("Generated a label outside FIRE_CLASSES")

    df.to_csv(output_file, index=False)
    print(f"Labeled hotspots: {len(df)}")
    print(df["fire_context"].value_counts())
    print(f"Unknown/review rows: {unknown_count}")
    print(f"Saved to {output_file}")
    return df


if __name__ == "__main__":
    create_labels()
