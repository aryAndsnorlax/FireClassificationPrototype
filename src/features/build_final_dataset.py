"""Validate and publish the Module 2 training dataset."""
from __future__ import annotations

import pandas as pd
from src.utils.config import DATA_PROCESSED, FIRE_CLASSES

INPUT_FILE = DATA_PROCESSED / "labeled_hotspots.csv"
OUTPUT_FILE = DATA_PROCESSED / "final_fire_dataset.csv"


def build_final_dataset() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE)
    required = {"fire_context", "label_confidence", "latitude", "longitude", "acq_date"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Final dataset is missing required columns: {sorted(missing)}")
    if df["fire_context"].isna().any():
        raise RuntimeError("Final dataset contains unlabeled rows")
    if not set(df["fire_context"].unique()).issubset(set(FIRE_CLASSES)):
        raise RuntimeError("Final dataset contains unsupported fire classes")
    if df.duplicated().any():
        print(f"Warning: {int(df.duplicated().sum())} exact duplicate rows detected")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} training rows to {OUTPUT_FILE}")
    print(df["fire_context"].value_counts())
    return df


if __name__ == "__main__":
    build_final_dataset()
