"""
Train an XGBoost classifier on the engineered features + weak labels
produced by src/labeling/rule_based_labels.py.
"""
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.utils.config import DATA_PROCESSED, MODELS_DIR, FIRE_CLASSES

FEATURE_COLUMNS = [
    "distance_to_facility_m",
    "frp",
    "brightness",       # or bright_ti4/bright_ti5 depending on sensor
    "confidence",
    "persistence_score",
    "frp_ratio_to_baseline",
    "cluster_size",
]
CATEGORICAL_COLUMNS = ["lc_class", "nearest_facility_type", "daynight"]
TARGET_COLUMN = "predicted_class"


def build_training_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df = pd.get_dummies(df, columns=CATEGORICAL_COLUMNS, dummy_na=True)
    feature_cols = FEATURE_COLUMNS + [
        c for c in df.columns if any(c.startswith(cat + "_") for cat in CATEGORICAL_COLUMNS)
    ]
    X = df[feature_cols].fillna(0)
    y = df[TARGET_COLUMN]
    return X, y


def train(df: pd.DataFrame):
    X, y = build_training_frame(df)

    le = LabelEncoder()
    le.fit(FIRE_CLASSES)
    y_enc = le.transform(y)

    # Split by location/time where possible in production — a plain random
    # split is a placeholder here; see docs/architecture.md for the
    # leakage-safe splitting strategy.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=len(FIRE_CLASSES),
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train)

    return model, le, (X_test, y_test), X.columns.tolist()


if __name__ == "__main__":
    df = pd.read_csv(DATA_PROCESSED / "labeled_hotspots.csv")
    model, label_encoder, test_set, feature_names = train(df)

    joblib.dump(
        {"model": model, "label_encoder": label_encoder, "feature_names": feature_names},
        MODELS_DIR / "xgboost_fire_classifier.pkl",
    )
    print(f"Model saved to {MODELS_DIR / 'xgboost_fire_classifier.pkl'}")
