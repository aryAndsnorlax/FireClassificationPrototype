"""
Run the trained classifier on new/incoming hotspots (used by the API
ingestion scheduler to classify FIRMS data as it arrives).
"""
import joblib
import pandas as pd

from src.utils.config import MODELS_DIR


def load_model(path=MODELS_DIR / "xgboost_fire_classifier.pkl"):
    return joblib.load(path)


def predict(df: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """
    df must already have the engineered features (see src/features/).
    Returns df with predicted_class and predicted_confidence columns added.
    """
    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    feature_names = bundle["feature_names"]

    X = pd.get_dummies(df)
    X = X.reindex(columns=feature_names, fill_value=0)

    proba = model.predict_proba(X)
    pred_idx = proba.argmax(axis=1)

    df = df.copy()
    df["predicted_class"] = label_encoder.inverse_transform(pred_idx)
    df["predicted_confidence"] = proba.max(axis=1)
    return df


if __name__ == "__main__":
    bundle = load_model()
    print("Model loaded. Use predict(df, bundle) on a feature-engineered DataFrame.")
