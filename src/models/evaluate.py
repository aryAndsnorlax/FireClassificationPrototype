"""Evaluate the trained XGBoost fire-context classifier."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from src.models.train import _prepare_frame
from src.utils.config import DATA_PROCESSED


MODEL_FILE = "models/xgboost_fire_classifier.pkl"
DATA_FILE = DATA_PROCESSED / "training_labeled_hotspots.csv"


def main():
    print("=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # Load model
    # ---------------------------------------------------------

    bundle = joblib.load(MODEL_FILE)

    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    feature_names = bundle["feature_names"]

    # ---------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------

    df = pd.read_csv(DATA_FILE)

    print(f"Dataset rows: {len(df)}")

    # ---------------------------------------------------------
    # Reproduce the exact spatial test split
    # ---------------------------------------------------------

    from src.models.train import _split

    train_idx, test_idx, split_strategy = _split(df)

    test_df = (
        df.iloc[test_idx]
        .reset_index(drop=True)
    )

    print(f"Split strategy: {split_strategy}")
    print(f"Test rows: {len(test_df)}")
    print()

    # ---------------------------------------------------------
    # Prepare test features
    # ---------------------------------------------------------

    X_test = _prepare_frame(
        test_df,
        feature_names,
    )

    y_test = label_encoder.transform(
        test_df["fire_context"].astype(str)
    )

    # ---------------------------------------------------------
    # Predict
    # ---------------------------------------------------------

    probabilities = model.predict_proba(X_test)

    predicted_indices = np.argmax(
        probabilities,
        axis=1,
    )

    # ---------------------------------------------------------
    # Apply industrial-fire threshold
    # ---------------------------------------------------------

    industrial_idx = int(
        label_encoder.transform(
            ["industrial_fire"]
        )[0]
    )

    industrial_threshold = bundle[
        "industrial_fire_threshold"
    ]

    # The normal multiclass prediction is retained unless
    # industrial_fire exceeds its tuned threshold.
    industrial_mask = (
        probabilities[:, industrial_idx]
        >= industrial_threshold
    )

    predicted_indices[
        industrial_mask
    ] = industrial_idx

    y_pred = predicted_indices

    # ---------------------------------------------------------
    # Convert labels back to class names
    # ---------------------------------------------------------

    class_names = list(
        label_encoder.classes_
    )

    # ---------------------------------------------------------
    # Overall accuracy
    # ---------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred,
    )

    print("=" * 60)
    print("OVERALL PERFORMANCE")
    print("=" * 60)

    print(
        f"Accuracy: {accuracy:.4f}"
    )

    print(
        f"Accuracy: {accuracy * 100:.2f}%"
    )

    print()

    # ---------------------------------------------------------
    # Classification report
    # ---------------------------------------------------------

    print("=" * 60)
    print("PER-CLASS PERFORMANCE")
    print("=" * 60)

    report = classification_report(
        y_test,
        y_pred,
        target_names=class_names,
        digits=4,
        zero_division=0,
    )

    print(report)

    # ---------------------------------------------------------
    # Confusion matrix
    # ---------------------------------------------------------

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=np.arange(
            len(class_names)
        ),
    )

    cm_df = pd.DataFrame(
        cm,
        index=[
            f"Actual: {c}"
            for c in class_names
        ],
        columns=[
            f"Predicted: {c}"
            for c in class_names
        ],
    )

    print("=" * 60)
    print("CONFUSION MATRIX")
    print("=" * 60)

    print(cm_df.to_string())

    print()

    # ---------------------------------------------------------
    # Prediction distribution
    # ---------------------------------------------------------

    predicted_labels = (
        label_encoder.inverse_transform(
            y_pred
        )
    )

    print("=" * 60)
    print("PREDICTED CLASS DISTRIBUTION")
    print("=" * 60)

    print(
        pd.Series(
            predicted_labels
        ).value_counts()
    )

    print()

    # ---------------------------------------------------------
    # Actual distribution
    # ---------------------------------------------------------

    print("=" * 60)
    print("ACTUAL TEST CLASS DISTRIBUTION")
    print("=" * 60)

    print(
        test_df["fire_context"]
        .value_counts()
    )

    print()

    print("=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()