from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi_firms_matches_2024.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi_firms_evidence_2024.csv"
)


# ============================================================
# Build evidence dataset
# ============================================================

def build_evidence():

    print("=" * 70)
    print("BUILDING FSI ↔ FIRMS EVIDENCE DATASET")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        low_memory=False
    )

    print(f"Input records: {len(df):,}")

    # --------------------------------------------------------
    # Ensure correct types
    # --------------------------------------------------------

    df["nearest_distance_km"] = pd.to_numeric(
        df["nearest_distance_km"],
        errors="coerce"
    )

    df["date_difference_days"] = pd.to_numeric(
        df["date_difference_days"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Match quality
    # --------------------------------------------------------

    conditions = [
        (
            df["firms_match_found"]
            & (df["nearest_distance_km"] <= 0.5)
        ),

        (
            df["firms_match_found"]
            & (df["nearest_distance_km"] > 0.5)
            & (df["nearest_distance_km"] <= 1.0)
        ),

        (
            df["firms_match_found"]
            & (df["nearest_distance_km"] > 1.0)
            & (df["nearest_distance_km"] <= 5.0)
        ),
    ]

    choices = [
        "strong",
        "moderate",
        "weak",
    ]

    df["match_quality"] = np.select(
        conditions,
        choices,
        default="none"
    )

    # --------------------------------------------------------
    # Explicit binary evidence flags
    # --------------------------------------------------------

    df["strong_match_500m"] = (
        df["firms_match_found"]
        & (df["nearest_distance_km"] <= 0.5)
    )

    df["moderate_match_1km"] = (
        df["firms_match_found"]
        & (df["nearest_distance_km"] > 0.5)
        & (df["nearest_distance_km"] <= 1.0)
    )

    df["weak_match_5km"] = (
        df["firms_match_found"]
        & (df["nearest_distance_km"] > 1.0)
        & (df["nearest_distance_km"] <= 5.0)
    )

    # --------------------------------------------------------
    # Same-day verification
    # --------------------------------------------------------

    df["same_day_match"] = (
        df["firms_match_found"]
        & (df["date_difference_days"] == 0)
    )

    # --------------------------------------------------------
    # Keep clean, useful columns
    # --------------------------------------------------------

    columns = [
        "fsi_id",
        "fsi_date",
        "fsi_lat",
        "fsi_lon",

        "firms_match_found",
        "firms_candidate_count",

        "nearest_distance_km",
        "date_difference_days",

        "same_day_match",

        "strong_match_500m",
        "moderate_match_1km",
        "weak_match_5km",

        "match_quality",

        "firms_latitude",
        "firms_longitude",
        "firms_instrument",
        "firms_satellite",
        "firms_frp",
        "firms_brightness",
        "firms_bright_t31",
        "firms_confidence",
        "firms_daynight",
    ]

    columns = [
        column
        for column in columns
        if column in df.columns
    ]

    result = df[columns].copy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("EVIDENCE DATASET COMPLETE")
    print("=" * 70)

    print(f"Total FSI records : {len(result):,}")

    print()
    print("Match quality:")

    print(
        result["match_quality"]
        .value_counts()
        .sort_index()
    )

    print()
    print("Same-day matches:")
    print(
        result["same_day_match"]
        .value_counts()
    )

    print()
    print("Strong matches (≤500 m):")
    print(
        result["strong_match_500m"].sum()
    )

    print()
    print("Moderate matches (500 m–1 km):")
    print(
        result["moderate_match_1km"].sum()
    )

    print()
    print("Weak matches (1–5 km):")
    print(
        result["weak_match_5km"].sum()
    )

    print()
    print("No FIRMS candidate:")
    print(
        (result["match_quality"] == "none").sum()
    )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    build_evidence()