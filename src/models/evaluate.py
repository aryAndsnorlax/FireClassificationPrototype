"""
Evaluate the trained classifier: confusion matrix, per-class precision/recall,
and SHAP feature importance. Recall on industrial_fire (accidents) is the
highest-priority metric — false negatives there are the costly failure mode.
"""
import joblib
import shap
from sklearn.metrics import classification_report, confusion_matrix

from src.utils.config import MODELS_DIR


def evaluate(model, label_encoder, X_test, y_test):
    y_pred = model.predict(X_test)

    print("Classification report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    return y_pred


def explain(model, X_sample):
    """Run SHAP to sanity-check the model is using sensible features."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    return shap_values


if __name__ == "__main__":
    bundle = joblib.load(MODELS_DIR / "xgboost_fire_classifier.pkl")
    model, label_encoder = bundle["model"], bundle["label_encoder"]

    # NOTE: in a real run, persist X_test/y_test from train.py instead of
    # retraining/reloading — this is a scaffold placeholder.
    print("Load your held-out test set and call evaluate(model, label_encoder, X_test, y_test)")
