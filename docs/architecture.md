# Architecture

## Pipeline overview

```
FIRMS API ──┐
OSM Overpass ┼─► src/ingestion ─► data/raw
Land cover ──┘

data/raw ─► src/features (spatial_join, temporal_features, clustering) ─► data/interim

data/interim ─► src/labeling (rule_based_labels.py) ─► data/processed/labeled_hotspots.csv

data/processed ─► src/models/train.py ─► models/xgboost_fire_classifier.pkl

models/*.pkl ─► api/scheduler/ingest_job.py (runs every 3h)
                   │
                   ▼
              PostGIS (api/db)
                   │
                   ▼
           FastAPI (api/routers) ──► frontend (Leaflet map)
```

## Key design decisions

- **Weak labeling before ML**: there is no pre-labeled dataset for this
  problem. `src/labeling/rule_based_labels.py` encodes the decision logic
  by hand first — this is both a working baseline classifier and the
  source of training labels for the XGBoost model in `src/models/train.py`.

- **Grid-based persistence/baseline features**: `src/features/temporal_features.py`
  buckets hotspots into ~1km grid cells to compute how often a location
  has been detected historically and how far today's FRP deviates from
  that location's own baseline. This is what separates "normal flare" from
  "possible accident" at the *same* facility.

- **Leakage-safe splitting**: when training the model for real, split
  train/test by location (grid_id) or by time window, not randomly — a
  persistent flare's hundreds of near-identical detections must not leak
  across the split, or the model will look artificially accurate.

- **Feature parity between training and inference**: `api/scheduler/ingest_job.py`
  must run the *same* feature pipeline (`src/features/`) used during
  training before calling `predict()`. The scaffold leaves a TODO here —
  this is one of the most common real-world bugs (train/serve skew).

## Where to focus effort

Per the project checklist, Phase 1-2 (data collection + labeling) is
where most of the real work and most of the risk lives. The modeling
step (Phase 4) is comparatively fast once good features and labels exist.
