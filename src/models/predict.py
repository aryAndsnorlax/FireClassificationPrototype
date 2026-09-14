"""Inference contract for the persisted Module 2 classifier."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from src.utils.config import MODELS_DIR
from src.models.train import _prepare_frame


def load_model(path=MODELS_DIR / "xgboost_fire_classifier.pkl"):
    """Load the model bundle produced by ``src.models.train``."""
    return joblib.load(path)


def predict(df: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """Predict fire context for an engineered hotspot dataframe.

    Required input schema:
      numeric/categorical features listed in ``bundle['input_schema']``.
      Missing optional feature columns are filled with zero/``__missing__``;
      extra columns are ignored. The dataframe must contain enough geographic
      and FIRMS-derived features to have meaningful predictions.

    Returns the original dataframe plus:
      - predicted_class
      - predicted_confidence
      - industrial_fire_probability
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(bundle, dict) or not {"model", "label_encoder", "feature_names"}.issubset(bundle):
        raise ValueError("Invalid model bundle")

    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    feature_names = bundle["feature_names"]

    X = _prepare_frame(df, feature_names)
    proba = model.predict_proba(X)
    pred_idx = proba.argmax(axis=1)
    threshold = float(bundle.get("industrial_fire_threshold", 0.50))

    if "industrial_fire" in label_encoder.classes_:
        industrial_idx = int(label_encoder.transform(["industrial_fire"])[0])
        industrial_mask = proba[:, industrial_idx] >= threshold
        pred_idx[industrial_mask] = industrial_idx
        industrial_probability = proba[:, industrial_idx]
    else:
        industrial_probability = [0.0] * len(df)

    result = df.copy()
    result["predicted_class"] = label_encoder.inverse_transform(pred_idx)
    result["predicted_confidence"] = proba[np.arange(len(result)), pred_idx]
    result["industrial_fire_probability"] = industrial_probability
    return result


if __name__ == "__main__":
    bundle = load_model()
    print("Model loaded. Call predict(engineered_df, bundle).")
