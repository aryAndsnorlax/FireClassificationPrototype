import pandas as pd

from src.utils.config import DATA_PROCESSED


# --------------------------------------------------
# File paths
# --------------------------------------------------

INPUT_FILE = DATA_PROCESSED / "final_fire_dataset.csv"

OUTPUT_FILE = DATA_PROCESSED / "ml_ready_fire_dataset.csv"


# --------------------------------------------------
# Columns to remove
# --------------------------------------------------

# These columns are not useful as direct ML features
# for the current prototype.

DROP_COLUMNS = [
    "bright_t31",
]


# --------------------------------------------------
# Convert acquisition time
# --------------------------------------------------

def create_time_features(df):
    """
    Convert FIRMS acquisition time into a useful
    numerical hour feature.
    """

    df = df.copy()

    # FIRMS acq_time is generally stored as HHMM
    time_values = (
        df["acq_time"]
        .astype(str)
        .str.zfill(4)
    )

    df["acquisition_hour"] = (
        time_values
        .str[:2]
        .astype(int)
    )

    return df


# --------------------------------------------------
# Main cleaning function
# --------------------------------------------------

def clean_dataset():

    print("=" * 80)
    print("ML DATASET PREPARATION")
    print("=" * 80)

    # --------------------------------------------------
    # Load dataset
    # --------------------------------------------------

    print()
    print("Loading final dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Original rows: {len(df)}")
    print(f"Original columns: {len(df.columns)}")

    # --------------------------------------------------
    # Create time feature
    # --------------------------------------------------

    print()
    print("Creating acquisition time feature...")

    df = create_time_features(df)

    # --------------------------------------------------
    # Remove mostly-missing columns
    # --------------------------------------------------

    print()
    print("Removing columns with insufficient data...")

    for column in DROP_COLUMNS:

        if column in df.columns:

            print(f"Removing: {column}")

            df = df.drop(
                columns=[column]
            )

    # --------------------------------------------------
    # Remove unnecessary identifier columns
    # --------------------------------------------------

    # These are useful for tracing/auditing but should
    # not be directly used by the model.

    ID_COLUMNS = [
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
        "satellite",
        "instrument",
        "version",
        "sensor",
        "worldcover_tile",
    ]

    print()
    print("Keeping geographic and metadata columns for now.")
    print("They will be handled during model preparation.")

    # --------------------------------------------------
    # Check target
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("TARGET VALIDATION")
    print("=" * 80)

    if "fire_context" not in df.columns:

        raise RuntimeError(
            "fire_context column not found."
        )

    print()
    print("Target column: fire_context")

    print()
    print("Class distribution:")

    print(
        df["fire_context"]
        .value_counts()
    )

    # --------------------------------------------------
    # Label confidence check
    # --------------------------------------------------

    if "label_confidence" in df.columns:

        print()
        print("Label confidence distribution:")

        print(
            df["label_confidence"]
            .value_counts()
            .sort_index()
        )

    # --------------------------------------------------
    # Missing values
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("MISSING VALUE CHECK")
    print("=" * 80)

    missing = df.isnull().sum()

    missing = missing[
        missing > 0
    ]

    if missing.empty:

        print("No missing values found.")

    else:

        print(missing)

    # --------------------------------------------------
    # Duplicate check
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("DUPLICATE CHECK")
    print("=" * 80)

    duplicates = df.duplicated().sum()

    print(
        f"Duplicate rows: {duplicates}"
    )

    # --------------------------------------------------
    # Dataset summary
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("FINAL DATASET SUMMARY")
    print("=" * 80)

    print()
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print()
    print("Columns:")

    for number, column in enumerate(
        df.columns,
        start=1
    ):

        print(
            f"{number}. {column}"
        )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("SAVING ML-READY DATASET")
    print("=" * 80)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("Saved to:")

    print(OUTPUT_FILE)

    print()
    print("=" * 80)
    print("ML DATASET PREPARATION COMPLETE")
    print("=" * 80)

    return df


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    clean_dataset()