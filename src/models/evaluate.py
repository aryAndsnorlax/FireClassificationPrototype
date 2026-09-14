"""Evaluation utilities for the Module 2 classifier, including SHAP."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, fbeta_score

from src.models.train import _prepare_frame
from src.utils.config import DATA_PROCESSED, MODELS_DIR


def evaluate(model, label_encoder, X_test, y_test, industrial_threshold: float = 0.50):
    """Print and return standard multiclass metrics plus industrial-fire F2."""
    probabilities = model.predict_proba(X_test)
    pred = probabilities.argmax(axis=1)
    if "industrial_fire" in label_encoder.classes_:
        industrial_idx = int(label_encoder.transform(["industrial_fire"])[0])
        pred[probabilities[:, industrial_idx] >= industrial_threshold] = industrial_idx
        industrial_f2 = fbeta_score(
            np.asarray(y_test) == industrial_idx,
            pred == industrial_idx,
            beta=2,
            zero_division=0,
        )
    else:
        industrial_f2 = 0.0

    report = classification_report(
        y_test,
        pred,
        labels=np.arange(len(label_encoder.classes_)),
        target_names=label_encoder.classes_,
        zero_division=0,
        output_dict=True,
    )
    matrix = confusion_matrix(y_test, pred, labels=np.arange(len(label_encoder.classes_)))
    return {"classification_report": report, "confusion_matrix": matrix.tolist(), "industrial_fire_f2": industrial_f2}


def explain(model, X_sample):
    """Return SHAP values for an XGBoost tree model."""
    import shap
    explainer = shap.TreeExplainer(model)
    return explainer.shap_values(X_sample)


def evaluate_saved_model():
    """Evaluate the persisted model on the labelled dataset using its saved split."""
    bundle = joblib.load(MODELS_DIR / "xgboost_fire_classifier.pkl")
    df = pd.read_csv(DATA_PROCESSED / "labeled_hotspots.csv")
    test_indices = bundle.get("test_row_indices")
    if not test_indices:
        raise RuntimeError("Model bundle does not contain held-out test indices")
    test_indices = [i for i in test_indices if i < len(df)]
    test_df = df.iloc[test_indices]
    X = _prepare_frame(test_df, bundle["feature_names"])
    y = bundle["label_encoder"].transform(test_df["fire_context"].astype(str))
    metrics = evaluate(
        bundle["model"],
        bundle["label_encoder"],
        X,
        y,
        bundle.get("industrial_fire_threshold", 0.50),
    )
    print(json.dumps(metrics, indent=2, default=str))
    return metrics


if __name__ == "__main__":
    evaluate_saved_model()
