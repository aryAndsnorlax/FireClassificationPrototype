import pandas as pd

from src.utils.config import DATA_INTERIM, DATA_PROCESSED


INPUT_FILE = DATA_INTERIM / "hotspots_features.csv"
OUTPUT_FILE = DATA_PROCESSED / "labeled_hotspots.csv"


def classify_hotspot(row):
    """
    Assign a prototype fire-context label using
    land cover, OSM proximity, and FIRMS characteristics.
    """

    landcover = str(row["landcover_class"]).lower()
    facility = str(row["nearest_facility_type"]).lower()

    facility_distance = row["distance_to_facility_m"]

    # --------------------------------------------------
    # 1. Agricultural context
    # --------------------------------------------------
    if landcover == "cropland":
        if pd.isna(facility_distance) or facility_distance > 1000:
            return "agricultural"

    # --------------------------------------------------
    # 2. Wildfire / vegetation context
    # --------------------------------------------------
    vegetation_classes = {
        "tree_cover",
        "shrubland",
        "grassland",
    }

    if landcover in vegetation_classes:
        if pd.isna(facility_distance) or facility_distance > 1000:
            return "wildfire"

    # --------------------------------------------------
    # 3. Mining context
    # --------------------------------------------------
    mining_types = {
        "quarry",
        "mine",
    }

    if facility in mining_types:
        return "mining"

    # --------------------------------------------------
    # 4. Industrial context
    # --------------------------------------------------
    industrial_types = {
        "industrial",
        "plant",
        "factory",
        "works",
        "refinery",
        "steelmaking",
        "metal_processing",
        "brickworks",
        "brickyard",
    }

    if facility in industrial_types:
        return "industrial"

    # --------------------------------------------------
    # 5. Built-up areas without clear facility context
    # --------------------------------------------------
    if landcover == "built_up":
        return "other"

    # --------------------------------------------------
    # 6. Bare/sparse land without clear mining context
    # --------------------------------------------------
    if landcover == "bare_sparse":
        return "other"

    # --------------------------------------------------
    # 7. Default
    # --------------------------------------------------
    return "other"


def calculate_label_confidence(row):
    """
    Estimate confidence in the rule-based label.

    This is NOT ML probability.
    It represents how strongly the available
    contextual evidence supports the rule.
    """

    label = row["fire_context"]

    landcover = str(row["landcover_class"]).lower()
    facility = str(row["nearest_facility_type"]).lower()

    distance = row["distance_to_facility_m"]

    # Strong agricultural evidence
    if label == "agricultural":
        if landcover == "cropland":
            return 0.80

    # Strong vegetation evidence
    if label == "wildfire":
        if landcover in {"tree_cover", "shrubland", "grassland"}:
            return 0.75

    # Strong mining evidence
    if label == "mining":
        if facility in {"quarry", "mine"}:
            return 0.85

    # Strong industrial evidence
    if label == "industrial":
        if facility in {
            "industrial",
            "plant",
            "factory",
            "works",
            "refinery",
            "steelmaking",
            "metal_processing",
            "brickworks",
            "brickyard",
        }:
            if not pd.isna(distance) and distance <= 500:
                return 0.90

            return 0.80

    # Weak / uncertain categories
    return 0.40


def create_labels():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    print(f"Input hotspots: {len(df)}")

    # Generate rule-based labels
    df["fire_context"] = df.apply(
        classify_hotspot,
        axis=1,
    )

    # Generate confidence score
    df["label_confidence"] = df.apply(
        calculate_label_confidence,
        axis=1,
    )

    # Save
    df.to_csv(OUTPUT_FILE, index=False)

    print()
    print("Fire-context distribution:")
    print(df["fire_context"].value_counts())

    print()
    print("Average confidence:")
    print(
        df.groupby("fire_context")["label_confidence"]
        .mean()
        .round(2)
    )

    print()
    print(f"Labeled hotspots: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_labels()