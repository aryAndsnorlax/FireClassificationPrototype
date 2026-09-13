"""
Periodic job: pull new FIRMS data, run the feature pipeline + trained model,
and upsert classified hotspots into PostGIS. Wired up in api/main.py via
APScheduler.
"""
from apscheduler.schedulers.background import BackgroundScheduler

from src.ingestion.fetch_firms import fetch_all_sensors
from src.models.predict import load_model, predict
from api.db.session import SessionLocal
from api.db.models import Hotspot


def run_ingest_cycle():
    """One full cycle: fetch -> feature-engineer -> classify -> store."""
    print("[ingest_job] Fetching latest FIRMS data...")
    raw_df = fetch_all_sensors(day_range=1)

    # TODO: run the same feature pipeline used in training
    # (src/features/spatial_join.py, temporal_features.py, clustering.py)
    # against raw_df before calling predict(), so features match at inference time.
    features_df = raw_df  # placeholder — replace with engineered features

    bundle = load_model()
    classified_df = predict(features_df, bundle)

    db = SessionLocal()
    try:
        for _, row in classified_df.iterrows():
            db.add(Hotspot(
                latitude=row["latitude"],
                longitude=row["longitude"],
                acq_date=row.get("acq_date"),
                frp=row.get("frp"),
                predicted_class=row.get("predicted_class"),
                predicted_confidence=row.get("predicted_confidence"),
                is_anomaly=row.get("predicted_class") == "industrial_fire",
            ))
        db.commit()
        print(f"[ingest_job] Stored {len(classified_df)} classified hotspots.")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_ingest_cycle, "interval", hours=3)
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    run_ingest_cycle()
