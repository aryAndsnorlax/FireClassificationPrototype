"""
Rule-based weak labeling: converts engineered features into a first-pass
class label per hotspot. This is both a standalone baseline classifier
(demoable on day 1) and the source of training labels for the ML model.

Mirrors the decision logic:
  1. Near a known industrial facility?
       -> persistent (high detection frequency) => persistent_industrial
       -> FRP far above baseline               => industrial_fire (accident)
       -> otherwise                             => industrial (normal variation)
  2. Not near a facility:
       -> cropland + stubble-burning season/region => agricultural_burning
       -> forest/scrub land cover                  => wildfire
       -> known mining land cover                  => coal_seam_fire
       -> otherwise                                 => unknown
"""
import pandas as pd

from src.utils.config import (
    FACILITY_PROXIMITY_M,
    PERSISTENCE_FREQ_THRESHOLD,
    FRP_ANOMALY_RATIO,
    DATA_PROCESSED,
    DATA_INTERIM,
)

# States/months associated with crop residue burning — tune against
# CPCB/PUSA published stubble-burning windows.
STUBBLE_BURNING_STATES = {"Punjab", "Haryana", "Uttar Pradesh"}
STUBBLE_BURNING_MONTHS = {10, 11}


def label_row(row: pd.Series) -> str:
    near_facility = row.get("distance_to_facility_m", float("inf")) <= FACILITY_PROXIMITY_M

    if near_facility:
        if row.get("persistence_score", 0) >= PERSISTENCE_FREQ_THRESHOLD:
            if row.get("frp_ratio_to_baseline", 1.0) >= FRP_ANOMALY_RATIO:
                return "industrial_fire"  # sudden spike even at a persistent source
            return "persistent_industrial"
        if row.get("frp_ratio_to_baseline", 1.0) >= FRP_ANOMALY_RATIO:
            return "industrial_fire"
        return "persistent_industrial"  # new/rare detection near facility, treat cautiously

    lc_class = str(row.get("lc_class", "")).lower()
    state = row.get("state", "")
    month = pd.to_datetime(row.get("acq_date")).month if row.get("acq_date") else None

    if lc_class == "cropland":
        if state in STUBBLE_BURNING_STATES and month in STUBBLE_BURNING_MONTHS:
            return "agricultural_burning"
        return "unknown"  # cropland fire outside expected season — flag for review

    if lc_class in {"forest", "scrub", "grassland"}:
        return "wildfire"

    if lc_class == "mining":
        return "coal_seam_fire"

    return "unknown"


def apply_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["predicted_class"] = df.apply(label_row, axis=1)
    return df


if __name__ == "__main__":
    input_path = DATA_INTERIM / "hotspots_with_cluster_features.csv"
    df = pd.read_csv(input_path)
    df = apply_labels(df)
    out_path = DATA_PROCESSED / "labeled_hotspots.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} labeled hotspots to {out_path}")
    print(df["predicted_class"].value_counts())
