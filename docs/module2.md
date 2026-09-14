# Module 2 — Feature Engineering & ML Classification

## Scope

Module 2 converts Module 1's cleaned FIRMS/geospatial data into a weakly-labelled training set and an XGBoost classifier.

Pipeline:

```text
Module 1 cleaned FIRMS + OSM + land-cover data
        |
        v
spatial_join.py
        |
        v
integrate_features.py
        |
        v
temporal_features.py
        |
        v
clustering.py
        |
        v
rule_based_labels.py
        |
        +--> data/processed/labeled_hotspots.csv
        |
        v
train.py
        |
        +--> models/xgboost_fire_classifier.pkl
        |
        v
evaluate.py / predict.py
```

## Official target classes

The classifier uses the six classes defined in `src/utils/config.py`:

- `industrial_fire`
- `persistent_industrial`
- `coal_seam_fire`
- `agricultural_burning`
- `wildfire`
- `unknown`

## Features

Spatial:
- nearest facility distance/type
- category-specific facility distances
- land-cover class

Temporal:
- grid-based persistence count
- active days
- persistence score
- FRP median baseline
- FRP deviation
- FRP ratio to baseline

Spatial event:
- date-scoped DBSCAN cluster ID
- cluster size

FIRMS:
- FRP
- brightness / confidence where available
- acquisition hour

## Weak labels

Rules are evidence-based and deliberately conservative. Industrial-fire labels require facility context and/or a strong FRP anomaly. Persistent industrial sources require repeated detections. Cropland and vegetation detections away from facilities are labelled agricultural burning and wildfire respectively. Ambiguous records are `unknown` rather than being forced into a class.

`label_confidence` is rule evidence strength, **not** an ML probability. It is used as a sample weight during training.

## Leakage-safe model split

If `grid_id` is available, the primary train/test split is grouped by grid so detections from the same location do not appear in both sets. A stratified random split is used only as a fallback when there are too few groups.

The industrial-fire threshold is tuned on a validation subset using F2 score, then the model is refit on the complete training side. The held-out test rows are not used for threshold selection.

## Inference contract

```python
from src.models.predict import load_model, predict

bundle = load_model()
result = predict(engineered_dataframe, bundle)
```

The saved bundle contains `input_schema`, `feature_names`, the class encoder and the tuned `industrial_fire_threshold`. `predict()` adds:

- `predicted_class`
- `predicted_confidence`
- `industrial_fire_probability`

Missing optional feature columns are filled safely; extra columns are ignored.

## Run order

After Module 1 produces the required input files:

```bash
python -m src.features.spatial_join
python -m src.features.integrate_features
python -m src.features.temporal_features
python -m src.features.clustering
python -m src.labeling.rule_based_labels
python -m src.features.build_final_dataset
python -m src.models.train
python -m src.models.evaluate
```

The final training contract is `data/processed/labeled_hotspots.csv`. The real model artifact is produced only after the actual project data is available; no synthetic model should be committed as a production artifact.
