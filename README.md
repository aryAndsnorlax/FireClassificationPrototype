python# AI-Based Detection & Classification of Industrial Fires (India)

Classifies NASA FIRMS thermal hotspots over India into industrial fires,
persistent industrial thermal sources (flares/kilns), coal-seam/mine fires,
agricultural burning, and wildfires — by fusing FIRMS thermal data with
OSM industrial infrastructure, land cover, and historical detection patterns.

## Quick start

```bash
# 1. Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env
# fill in FIRMS_MAP_KEY, DATABASE_URL, etc.

# 3. Pull raw data
python -m src.ingestion.fetch_firms
python -m src.ingestion.fetch_osm
python -m src.ingestion.fetch_landcover

# 4. Build features + weak labels (see notebooks/ for exploration first)
python -m src.features.spatial_join
python -m src.features.temporal_features
python -m src.labeling.rule_based_labels

# 5. Train the model
python -m src.models.train
python -m src.models.evaluate

# 6. Run the backend
uvicorn api.main:app --reload

# 7. Run the frontend
# open frontend/index.html, or serve it via any static server
```

Or run everything containerized:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Project layout

See `docs/architecture.md` for the full pipeline explanation.

- `data/` — raw → interim → processed datasets
- `notebooks/` — exploration only, nothing here is required at runtime
- `src/` — ingestion, feature engineering, labeling, modeling (the core pipeline)
- `api/` — FastAPI backend serving classified hotspots + alerts from PostGIS
- `frontend/` — Leaflet.js map dashboard
- `docker/` — one-command local deployment
- `tests/` — unit tests for features and API

## Status

Scaffold only — fill in each module per `docs/architecture.md` and the
project checklist.
