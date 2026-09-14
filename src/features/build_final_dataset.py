import pandas as pd
from src.utils.config import DATA_INTERIM, DATA_PROCESSED


TEMPORAL_FILE = DATA_INTERIM / "hotspots_with_temporal_features.csv"
LABEL_FILE = DATA_PROCESSED / "labeled_hotspots.csv"

OUTPUT_FILE = DATA_PROCESSED / "final_fire_dataset.csv"


MERGE_KEYS = [
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "sensor",
]


def normalize_keys(df):
    df = df.copy()

    df["acq_date"] = pd.to_datetime(
        df["acq_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["acq_time"] = df["acq_time"].astype(str).str.strip()

    return df


def build_final_dataset():
    print("Loading datasets...")

    temporal = pd.read_csv(TEMPORAL_FILE)
    labels = pd.read_csv(LABEL_FILE)

    print(f"Temporal dataset rows: {len(temporal)}")
    print(f"Label dataset rows: {len(labels)}")

    temporal = normalize_keys(temporal)
    labels = normalize_keys(labels)

    # Keep only label information that is missing
    # from the temporal dataset.
    label_columns = MERGE_KEYS + [
        "fire_context",
        "label_confidence",
    ]

    labels = labels[label_columns]

    print("\nMerging labels with temporal features...")

    final = temporal.merge(
        labels,
        on=MERGE_KEYS,
        how="left",
        validate="one_to_one",
    )

    print(f"Final dataset rows: {len(final)}")
    print(f"Final dataset columns: {len(final.columns)}")

    # Check whether every hotspot received a label
    missing_labels = final["fire_context"].isna().sum()
    missing_confidence = final["label_confidence"].isna().sum()

    print("\nLabel validation:")
    print(f"Missing fire_context: {missing_labels}")
    print(f"Missing label_confidence: {missing_confidence}")

    print("\nFire-context distribution:")

    print(final["fire_context"].value_counts(dropna=False))

    print("\nSaving final dataset...")

    final.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved to:")
    print(OUTPUT_FILE)

    return final


if __name__ == "__main__":
    build_final_dataset()