"""Train, tune and persist the XGBoost fire-context classifier."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import fbeta_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.utils.config import DATA_PROCESSED, MODELS_DIR, FIRE_CLASSES


TARGET_COLUMN = "fire_context"

# Categorical features.
# Sensor and instrument are important because FIRMS thermal fields
# differ between VIIRS and MODIS observations.
CATEGORICAL_COLUMNS = [
    "landcover_class",
    "nearest_facility_type",
    "daynight",
    "sensor",
    "instrument",
]

# Numerical features used by the classifier.
NUMERIC_COLUMNS = [
    "distance_to_facility_m",
    "distance_to_industrial_m",
    "distance_to_plant_m",
    "distance_to_quarry_m",
    "distance_to_works_m",
    "distance_to_factory_m",
    "distance_to_mine_m",
    "distance_to_brickyard_m",
    "distance_to_brickworks_m",
    "frp",
    "brightness",
    "bright_ti4",
    "bright_ti5",
    "confidence",
    "persistence_count",
    "active_days",
    "persistence_score",
    "mean_frp",
    "median_frp",
    "max_frp",
    "frp_baseline",
    "frp_deviation",
    "frp_ratio_to_baseline",
    "cluster_size",
    "acquisition_hour",
]

# These indicate which thermal measurement family is applicable.
# This prevents missing sensor-specific values from being confused
# with actual zero measurements.
THERMAL_INDICATOR_COLUMNS = [
    "has_viirs_thermal",
    "has_modis_thermal",
]

MODEL_FILE = MODELS_DIR / "xgboost_fire_classifier.pkl"
METADATA_FILE = MODELS_DIR / "xgboost_fire_classifier.metadata.json"


def _prepare_frame(
    df: pd.DataFrame,
    feature_names: list[str] | None = None,
):
    """Convert raw feature dataframe into an ML-ready numeric dataframe."""

    frame = df.copy()

    # Backward compatibility:
    # some older datasets may use lc_class instead of landcover_class.
    if "landcover_class" not in frame.columns and "lc_class" in frame.columns:
        frame["landcover_class"] = frame["lc_class"]

    # Make sure all expected numerical columns exist and are numeric.
    for col in NUMERIC_COLUMNS:
        if col not in frame.columns:
            frame[col] = np.nan

        frame[col] = pd.to_numeric(
            frame[col],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # Sensor-aware thermal availability indicators
    # ---------------------------------------------------------
    #
    # VIIRS:
    #   bright_ti4
    #   bright_ti5
    #
    # MODIS:
    #   brightness
    #   bright_t31
    #
    # Missing values are expected because these fields are
    # sensor-specific.
    frame["has_viirs_thermal"] = (
        frame["bright_ti4"].notna()
        | frame["bright_ti5"].notna()
    ).astype(int)

    frame["has_modis_thermal"] = (
        frame["brightness"].notna()
        | frame["bright_t31"].notna()
    ).astype(int)

    # ---------------------------------------------------------
    # Categorical features
    # ---------------------------------------------------------

    categorical_present = [
        c for c in CATEGORICAL_COLUMNS
        if c in frame.columns
    ]

    if categorical_present:
        frame[categorical_present] = (
            frame[categorical_present]
            .fillna("__missing__")
            .astype(str)
        )

        frame = pd.get_dummies(
            frame,
            columns=categorical_present,
            dummy_na=False,
        )

    # ---------------------------------------------------------
    # Select ML features
    # ---------------------------------------------------------

    feature_cols = [
        c
        for c in frame.columns
        if (
            c in NUMERIC_COLUMNS
            or c in THERMAL_INDICATOR_COLUMNS
            or any(
                c.startswith(cat + "_")
                for cat in CATEGORICAL_COLUMNS
            )
        )
    ]

    X = frame[feature_cols].copy()

    # Convert everything to numeric.
    X = X.apply(
        pd.to_numeric,
        errors="coerce",
    )

    # XGBoost can handle NaN, but filling missing values here
    # keeps the feature matrix deterministic and compatible
    # with the stored feature schema.
    X = X.fillna(0.0)

    # During validation/test prediction, force exactly the
    # same columns used during training.
    if feature_names is not None:
        X = X.reindex(
            columns=feature_names,
            fill_value=0.0,
        )

    return X


def build_training_frame(df: pd.DataFrame):
    """Build X and y from a labelled dataframe."""

    if TARGET_COLUMN not in df:
        raise ValueError(
            f"Missing target column: {TARGET_COLUMN}"
        )

    return (
        _prepare_frame(df),
        df[TARGET_COLUMN].astype(str),
    )


def _split(df: pd.DataFrame):
    """Create a spatially-aware train/test split."""

    y = df[TARGET_COLUMN].astype(str)

    groups = (
        df["grid_id"].astype(str)
        if "grid_id" in df.columns
        else None
    )

    if groups is not None and groups.nunique() >= 5:

        # Group splitting prevents observations from the same
        # spatial grid appearing in both train and test.
        #
        # Multiple deterministic seeds are tried because a random
        # group split can occasionally put an entire class into
        # the test set.
        required_classes = set(y.unique())

        for seed in range(42, 142):

            splitter = GroupShuffleSplit(
                n_splits=1,
                test_size=0.20,
                random_state=seed,
            )

            train_idx, test_idx = next(
                splitter.split(
                    df,
                    groups=groups,
                )
            )

            train_classes = set(
                y.iloc[train_idx].unique()
            )

            if required_classes.issubset(train_classes):
                return (
                    np.asarray(train_idx),
                    np.asarray(test_idx),
                    "group_grid_id",
                )

        # If no group split contains all classes in training,
        # fall back to stratified random splitting.

    indices = np.arange(len(df))

    stratify = (
        y
        if y.value_counts().min() >= 2
        else None
    )

    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.20,
        random_state=42,
        stratify=stratify,
    )

    return (
        np.asarray(train_idx),
        np.asarray(test_idx),
        "stratified_random",
    )


def _make_model(num_classes: int) -> XGBClassifier:
    """Create the XGBoost multiclass classifier."""

    return XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=num_classes,
        eval_metric="mlogloss",
        tree_method="hist",
        random_state=42,
        n_jobs=2,
    )


def _fit(
    model,
    X,
    y,
    sample_weight=None,
):
    """Fit the XGBoost model."""

    kwargs = {}

    if sample_weight is not None:
        kwargs["sample_weight"] = sample_weight

    model.fit(
        X,
        y,
        **kwargs,
    )

    return model


def tune_industrial_threshold(
    model,
    X_val,
    y_val,
    label_encoder,
) -> float:
    """Choose industrial-fire probability threshold using validation F2."""

    if "industrial_fire" not in label_encoder.classes_:
        return 0.50

    industrial_idx = int(
        label_encoder.transform(
            ["industrial_fire"]
        )[0]
    )

    probabilities = model.predict_proba(X_val)

    y_true = (
        np.asarray(y_val) == industrial_idx
    ).astype(int)

    # No positive industrial-fire examples.
    if y_true.sum() == 0:
        return 0.50

    best_threshold = 0.50
    best_score = -1.0

    for threshold in np.arange(
        0.20,
        0.81,
        0.02,
    ):

        y_pred = (
            probabilities[:, industrial_idx]
            >= threshold
        ).astype(int)

        score = fbeta_score(
            y_true,
            y_pred,
            beta=2,
            zero_division=0,
        )

        if score > best_score:
            best_score = score
            best_threshold = float(threshold)

    return best_threshold


def train(df: pd.DataFrame):
    """Train the complete fire-context classifier."""

    # ---------------------------------------------------------
    # Required columns
    # ---------------------------------------------------------

    missing = [
        c
        for c in [
            TARGET_COLUMN,
            "latitude",
            "longitude",
        ]
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required training columns: {missing}"
        )

    # ---------------------------------------------------------
    # Validate labels
    # ---------------------------------------------------------

    if not set(
        df[TARGET_COLUMN]
        .dropna()
        .astype(str)
    ).issubset(set(FIRE_CLASSES)):

        raise ValueError(
            "Training data contains labels outside FIRE_CLASSES"
        )

    df = df.dropna(
        subset=[TARGET_COLUMN]
    ).copy()

    if len(df) < 30:
        raise ValueError(
            "At least 30 labelled rows are required "
            "for a reliable train/validation/test split"
        )

    observed_classes = set(
        df[TARGET_COLUMN].astype(str)
    )

    missing_classes = [
        c
        for c in FIRE_CLASSES
        if c not in observed_classes
    ]

    if missing_classes:
        raise ValueError(
            f"Training data is missing FIRE_CLASSES: "
            f"{missing_classes}"
        )

    # ---------------------------------------------------------
    # Print dataset information
    # ---------------------------------------------------------

    print("=" * 60)
    print("TRAINING DATASET")
    print("=" * 60)
    print(f"Rows: {len(df)}")
    print(f"Classes: {len(observed_classes)}")
    print()
    print("Class distribution:")

    print(
        df[TARGET_COLUMN]
        .value_counts()
        .to_string()
    )

    print()

    if "sensor" in df.columns:
        print("Sensor distribution:")
        print(
            df["sensor"]
            .value_counts()
            .to_string()
        )

        print()

    # ---------------------------------------------------------
    # Train/test split
    # ---------------------------------------------------------

    train_idx, test_idx, split_strategy = _split(df)

    train_df = (
        df.iloc[train_idx]
        .reset_index(drop=True)
    )

    test_df = (
        df.iloc[test_idx]
        .reset_index(drop=True)
    )

    print(
        f"Split strategy: {split_strategy}"
    )

    print(
        f"Training rows: {len(train_df)}"
    )

    print(
        f"Test rows: {len(test_df)}"
    )

    # ---------------------------------------------------------
    # Validation split
    # ---------------------------------------------------------

    val_stratify = (
        train_df[TARGET_COLUMN]
        if train_df[TARGET_COLUMN]
        .value_counts()
        .min() >= 2
        else None
    )

    fit_idx, val_idx = train_test_split(
        np.arange(len(train_df)),
        test_size=0.20,
        random_state=43,
        stratify=val_stratify,
    )

    fit_df = train_df.iloc[fit_idx]
    val_df = train_df.iloc[val_idx]

    # ---------------------------------------------------------
    # Encode labels
    # ---------------------------------------------------------

    label_encoder = LabelEncoder()

    label_encoder.fit(FIRE_CLASSES)

    y_fit = label_encoder.transform(
        fit_df[TARGET_COLUMN].astype(str)
    )

    y_val = label_encoder.transform(
        val_df[TARGET_COLUMN].astype(str)
    )

    y_test = label_encoder.transform(
        test_df[TARGET_COLUMN].astype(str)
    )

    # ---------------------------------------------------------
    # Build feature matrices
    # ---------------------------------------------------------

    X_fit = _prepare_frame(
        fit_df
    )

    X_val = _prepare_frame(
        val_df,
        X_fit.columns.tolist(),
    )

    X_test = _prepare_frame(
        test_df,
        X_fit.columns.tolist(),
    )

    print(
        f"ML features: {X_fit.shape[1]}"
    )

    print()

    print("Thermal feature availability:")

    for column in [
        "bright_ti4",
        "bright_ti5",
        "brightness",
        "bright_t31",
    ]:

        if column in fit_df.columns:
            available = int(
                fit_df[column].notna().sum()
            )

            print(
                f"  {column}: "
                f"{available}/{len(fit_df)}"
            )

    print()

    # ---------------------------------------------------------
    # Weak-label confidence weights
    # ---------------------------------------------------------

    weights = pd.to_numeric(
        fit_df.get(
            "label_confidence",
            1.0,
        ),
        errors="coerce",
    ).fillna(
        0.5
    ).clip(
        0.25,
        1.0,
    ).to_numpy()

    # ---------------------------------------------------------
    # Initial model for threshold tuning
    # ---------------------------------------------------------

    model = _fit(
        _make_model(len(FIRE_CLASSES)),
        X_fit,
        y_fit,
        weights,
    )

    threshold = tune_industrial_threshold(
        model,
        X_val,
        y_val,
        label_encoder,
    )

    print(
        f"Selected industrial-fire "
        f"threshold: {threshold:.2f}"
    )

    # ---------------------------------------------------------
    # Refit using all training-side observations
    # ---------------------------------------------------------

    X_train_all = _prepare_frame(
        train_df,
        X_fit.columns.tolist(),
    )

    y_train_all = label_encoder.transform(
        train_df[TARGET_COLUMN].astype(str)
    )

    weights_all = pd.to_numeric(
        train_df.get(
            "label_confidence",
            1.0,
        ),
        errors="coerce",
    ).fillna(
        0.5
    ).clip(
        0.25,
        1.0,
    ).to_numpy()

    model = _fit(
        _make_model(len(FIRE_CLASSES)),
        X_train_all,
        y_train_all,
        weights_all,
    )

    # ---------------------------------------------------------
    # Model bundle
    # ---------------------------------------------------------

    bundle = {
        "model": model,
        "label_encoder": label_encoder,
        "feature_names": X_train_all.columns.tolist(),

        "input_schema": {
            "numeric": NUMERIC_COLUMNS,
            "categorical": CATEGORICAL_COLUMNS,
            "thermal_indicators": THERMAL_INDICATOR_COLUMNS,
            "target": TARGET_COLUMN,
        },

        "industrial_fire_threshold": threshold,

        "fire_classes": FIRE_CLASSES,

        "split_strategy": split_strategy,

        "test_row_indices": df.index[
            test_idx
        ].tolist(),

        "random_state": 42,
    }

    return (
        bundle,
        (X_test, y_test),
        df,
    )


def main():
    """Train and save the model."""

    # IMPORTANT:
    # This is the dedicated historical training dataset.
    # Production labelled_hotspots.csv is not modified.
    training_file = (
        DATA_PROCESSED
        / "training_labeled_hotspots.csv"
    )

    if not training_file.exists():
        raise FileNotFoundError(
            f"Training dataset not found: "
            f"{training_file}"
        )

    print(
        f"Loading training dataset: "
        f"{training_file}"
    )

    df = pd.read_csv(
        training_file
    )

    bundle, test_set, _ = train(df)

    # ---------------------------------------------------------
    # Save model
    # ---------------------------------------------------------

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        bundle,
        MODEL_FILE,
    )

    # ---------------------------------------------------------
    # Save metadata
    # ---------------------------------------------------------

    metadata = {
        k: v
        for k, v in bundle.items()
        if k not in {
            "model",
            "label_encoder",
        }
    }

    metadata["classes"] = list(
        bundle["label_encoder"].classes_
    )

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Final output
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("MODEL TRAINING COMPLETE")
    print("=" * 60)

    print(
        f"Model saved to: {MODEL_FILE}"
    )

    print(
        f"Metadata saved to: {METADATA_FILE}"
    )

    print(
        f"Industrial-fire threshold: "
        f"{bundle['industrial_fire_threshold']:.2f}"
    )

    print(
        f"Test rows: {len(test_set[1])}"
    )

    print(
        f"Number of ML features: "
        f"{len(bundle['feature_names'])}"
    )


if __name__ == "__main__":
    main()