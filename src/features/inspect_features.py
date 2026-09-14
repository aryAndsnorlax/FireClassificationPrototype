import pandas as pd

from src.utils.config import DATA_PROCESSED


INPUT_FILE = DATA_PROCESSED / "final_fire_dataset.csv"


def inspect_features():
    # --------------------------------------------------
    # Load final dataset
    # --------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print("=" * 80)
    print("FIRE HOTSPOT FEATURE INSPECTION")
    print("=" * 80)

    print()
    print(f"Total hotspots: {len(df)}")
    print(f"Total features: {len(df.columns)}")

    # --------------------------------------------------
    # Important columns for manual validation
    # --------------------------------------------------

    columns = [
        "latitude",
        "longitude",
        "fire_context",
        "label_confidence",
        "landcover_class",
        "nearest_facility_type",
        "distance_to_facility_m",
        "persistence_count",
        "active_days",
        "mean_frp",
        "max_frp",
    ]

    # Make sure all requested columns exist
    available_columns = [
        column
        for column in columns
        if column in df.columns
    ]

    missing_columns = [
        column
        for column in columns
        if column not in df.columns
    ]

    if missing_columns:
        print()
        print("WARNING: Missing columns:")

        for column in missing_columns:
            print(f"  - {column}")

    # --------------------------------------------------
    # Overall class distribution
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("FIRE CONTEXT DISTRIBUTION")
    print("=" * 80)

    print(
        df["fire_context"].value_counts()
    )

    # --------------------------------------------------
    # Detailed inspection by fire context
    # --------------------------------------------------

    for context in df["fire_context"].dropna().unique():

        print()
        print("=" * 80)
        print(f"CONTEXT: {context.upper()}")
        print("=" * 80)

        subset = df[
            df["fire_context"] == context
        ][available_columns].copy()

        print(
            subset.to_string(
                index=False
            )
        )

    # --------------------------------------------------
    # Suspicious / uncertain labels
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("LOW-CONFIDENCE LABELS")
    print("=" * 80)

    low_confidence = df[
        df["label_confidence"] < 0.70
    ][available_columns]

    if len(low_confidence) == 0:
        print("No low-confidence labels found.")
    else:
        print(
            low_confidence.to_string(
                index=False
            )
        )

    # --------------------------------------------------
    # Temporal feature summary by context
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("TEMPORAL FEATURES BY FIRE CONTEXT")
    print("=" * 80)

    summary = (
        df.groupby("fire_context")[
            [
                "persistence_count",
                "active_days",
                "mean_frp",
                "max_frp",
            ]
        ]
        .mean()
        .round(2)
    )

    print(summary)

    # --------------------------------------------------
    # Missing-value check
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("MISSING VALUE CHECK")
    print("=" * 80)

    missing_values = df.isnull().sum()
    missing_values = missing_values[
        missing_values > 0
    ]

    if missing_values.empty:
        print("No missing values found.")
    else:
        print(missing_values)

    # --------------------------------------------------
    # Data types
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("DATA TYPES")
    print("=" * 80)

    print(df.dtypes)

    # --------------------------------------------------
    # Duplicate check
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("DUPLICATE CHECK")
    print("=" * 80)

    duplicate_count = df.duplicated().sum()

    print(f"Duplicate rows: {duplicate_count}")

    # --------------------------------------------------
    # Final inspection message
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    inspect_features()