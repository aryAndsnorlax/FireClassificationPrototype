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
CATEGORICAL_COLUMNS = ["landcover_class", "nearest_facility_type", "daynight"]
NUMERIC_COLUMNS = [
    "distance_to_facility_m", "distance_to_industrial_m", "distance_to_plant_m",
    "distance_to_quarry_m", "distance_to_works_m", "distance_to_factory_m",
    "distance_to_mine_m", "distance_to_refinery_m", "distance_to_brickyard_m",
    "frp", "brightness", "bright_ti4", "bright_ti5", "confidence",
    "persistence_count", "active_days", "persistence_score", "mean_frp",
    "median_frp", "max_frp", "frp_baseline", "frp_deviation",
    "frp_ratio_to_baseline", "cluster_size", "acquisition_hour",
]

MODEL_FILE = MODELS_DIR / "xgboost_fire_classifier.pkl"
METADATA_FILE = MODELS_DIR / "xgboost_fire_classifier.metadata.json"


def _prepare_frame(df: pd.DataFrame, feature_names: list[str] | None = None):
    frame = df.copy()
    # Backward compatibility: normalize the old land-cover name once.
    if "landcover_class" not in frame.columns and "lc_class" in frame.columns:
        frame["landcover_class"] = frame["lc_class"]
    for col in NUMERIC_COLUMNS:
        if col not in frame:
            frame[col] = np.nan
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    categorical_present = [c for c in CATEGORICAL_COLUMNS if c in frame.columns]
    if categorical_present:
        frame[categorical_present] = frame[categorical_present].fillna("__missing__").astype(str)
        frame = pd.get_dummies(frame, columns=categorical_present, dummy_na=False)

    feature_cols = [c for c in frame.columns if c in NUMERIC_COLUMNS or any(c.startswith(cat + "_") for cat in CATEGORICAL_COLUMNS)]
    X = frame[feature_cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    if feature_names is not None:
        X = X.reindex(columns=feature_names, fill_value=0.0)
    return X


def build_training_frame(df: pd.DataFrame):
    if TARGET_COLUMN not in df:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")
    return _prepare_frame(df), df[TARGET_COLUMN].astype(str)


def _split(df: pd.DataFrame):
    y = df[TARGET_COLUMN].astype(str)
    groups = df["grid_id"].astype(str) if "grid_id" in df.columns else None
    if groups is not None and groups.nunique() >= 5:
        # Group splitting prevents the same spatial grid appearing in both
        # train and test. Try several deterministic seeds because a random
        # group split can otherwise place an entire class in the held-out
        # groups, leaving XGBoost with non-contiguous/missing class ids.
        required_classes = set(y.unique())
        for seed in range(42, 142):
            splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
            train_idx, test_idx = next(splitter.split(df, groups=groups))
            train_classes = set(y.iloc[train_idx].unique())
            if required_classes.issubset(train_classes):
                return np.asarray(train_idx), np.asarray(test_idx), "group_grid_id"
        # If the number/distribution of groups makes a class-complete group
        # split impossible, use a stratified random split rather than failing
        # with an invalid XGBoost label space.

    indices = np.arange(len(df))
    stratify = y if y.value_counts().min() >= 2 else None
    train_idx, test_idx = train_test_split(indices, test_size=0.20, random_state=42, stratify=stratify)
    return np.asarray(train_idx), np.asarray(test_idx), "stratified_random"


def _make_model(num_classes: int) -> XGBClassifier:
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


def _fit(model, X, y, sample_weight=None):
    kwargs = {}
    if sample_weight is not None:
        kwargs["sample_weight"] = sample_weight
    model.fit(X, y, **kwargs)
    return model


def tune_industrial_threshold(model, X_val, y_val, label_encoder) -> float:
    """Choose the industrial-fire probability threshold using validation F2."""
    if "industrial_fire" not in label_encoder.classes_:
        return 0.50
    industrial_idx = int(label_encoder.transform(["industrial_fire"])[0])
    probabilities = model.predict_proba(X_val)
    y_true = (np.asarray(y_val) == industrial_idx).astype(int)
    # If validation contains no positive industrial examples, there is no
    # meaningful threshold to tune. Keep the neutral default.
    if y_true.sum() == 0:
        return 0.50

    best_threshold, best_score = 0.50, -1.0
    for threshold in np.arange(0.20, 0.81, 0.02):
        y_pred = (probabilities[:, industrial_idx] >= threshold).astype(int)
        score = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return best_threshold


def train(df: pd.DataFrame):
    missing = [c for c in [TARGET_COLUMN, "latitude", "longitude"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required training columns: {missing}")

    # Unknown labels are deliberately retained as a review/other class, but
    # rows with invalid target values are rejected rather than silently mapped.
    if not set(df[TARGET_COLUMN].dropna().astype(str)).issubset(set(FIRE_CLASSES)):
        raise ValueError("Training data contains labels outside FIRE_CLASSES")
    df = df.dropna(subset=[TARGET_COLUMN]).copy()
    if len(df) < 30:
        raise ValueError("At least 30 labelled rows are required for a reliable train/validation/test split")
    observed_classes = set(df[TARGET_COLUMN].astype(str))
    missing_classes = [c for c in FIRE_CLASSES if c not in observed_classes]
    if missing_classes:
        raise ValueError(f"Training data is missing FIRE_CLASSES: {missing_classes}")

    train_idx, test_idx, split_strategy = _split(df)
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Validation split is used only for industrial threshold tuning.
    val_stratify = train_df[TARGET_COLUMN] if train_df[TARGET_COLUMN].value_counts().min() >= 2 else None
    fit_idx, val_idx = train_test_split(np.arange(len(train_df)), test_size=0.20, random_state=43, stratify=val_stratify)
    fit_df = train_df.iloc[fit_idx]
    val_df = train_df.iloc[val_idx]

    label_encoder = LabelEncoder()
    label_encoder.fit(FIRE_CLASSES)
    y_fit = label_encoder.transform(fit_df[TARGET_COLUMN].astype(str))
    y_val = label_encoder.transform(val_df[TARGET_COLUMN].astype(str))
    y_test = label_encoder.transform(test_df[TARGET_COLUMN].astype(str))

    X_fit = _prepare_frame(fit_df)
    X_val = _prepare_frame(val_df, X_fit.columns.tolist())
    X_test = _prepare_frame(test_df, X_fit.columns.tolist())

    weights = pd.to_numeric(fit_df.get("label_confidence", 1.0), errors="coerce").fillna(0.5).clip(0.25, 1.0).to_numpy()
    model = _fit(_make_model(len(FIRE_CLASSES)), X_fit, y_fit, weights)
    threshold = tune_industrial_threshold(model, X_val, y_val, label_encoder)

    # Refit using all train-side observations after threshold selection.
    X_train_all = _prepare_frame(train_df, X_fit.columns.tolist())
    y_train_all = label_encoder.transform(train_df[TARGET_COLUMN].astype(str))
    weights_all = pd.to_numeric(train_df.get("label_confidence", 1.0), errors="coerce").fillna(0.5).clip(0.25, 1.0).to_numpy()
    model = _fit(_make_model(len(FIRE_CLASSES)), X_train_all, y_train_all, weights_all)

    bundle = {
        "model": model,
        "label_encoder": label_encoder,
        "feature_names": X_train_all.columns.tolist(),
        "input_schema": {
            "numeric": NUMERIC_COLUMNS,
            "categorical": CATEGORICAL_COLUMNS,
            "target": TARGET_COLUMN,
        },
        "industrial_fire_threshold": threshold,
        "fire_classes": FIRE_CLASSES,
        "split_strategy": split_strategy,
        "test_row_indices": df.index[test_idx].tolist(),
        "random_state": 42,
    }
    return bundle, (X_test, y_test), df


def main():
    df = pd.read_csv(DATA_PROCESSED / "labeled_hotspots.csv")
    bundle, test_set, _ = train(df)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_FILE)
    metadata = {k: v for k, v in bundle.items() if k not in {"model", "label_encoder"}}
    metadata["classes"] = list(bundle["label_encoder"].classes_)
    METADATA_FILE.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(f"Model saved to {MODEL_FILE}")
    print(f"Industrial-fire threshold: {bundle['industrial_fire_threshold']:.2f}")
    print(f"Test rows: {len(test_set[1])}")


if __name__ == "__main__":
    main()
