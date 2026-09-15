"""
Periodic job:
1. Fetch latest FIRMS data
2. Run the same feature-engineering pipeline used during training
3. Run trained XGBoost model
4. Store classified hotspots in PostGIS
"""

from pathlib import Path
import subprocess
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from geoalchemy2 import WKTElement

from src.ingestion.fetch_firms import fetch_all_sensors
from src.models.predict import load_model, predict

from api.db.session import SessionLocal
from api.db.models import Hotspot


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_RAW = BASE_DIR / "data" / "raw"
DATA_INTERIM = BASE_DIR / "data" / "interim"


# ============================================================
# HELPER
# ============================================================

def run_module(module_name):
    """
    Run an existing project module exactly as it is normally
    run from the project root.

    Example:
        python -m src.ingestion.sample_landcover
    """

    print(f"[ingest_job] Running {module_name}...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module_name,
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:

        if result.stderr:
            print(result.stderr)

        raise RuntimeError(
            f"{module_name} failed with exit code "
            f"{result.returncode}"
        )


# ============================================================
# PRODUCTION FEATURE PIPELINE
# ============================================================

def run_production_feature_pipeline(raw_df):
    """
    Run the same feature-engineering stages used for training.

    Pipeline:

        FIRMS
          ↓
        Landcover
          ↓
        Spatial features
          ↓
        Temporal features
          ↓
        Clustering
          ↓
        features_df
    """

    print()
    print("[ingest_job] Starting feature pipeline...")

    # --------------------------------------------------------
    # 1. Save latest FIRMS data
    # --------------------------------------------------------

    firms_file = DATA_INTERIM / "firms_india.csv"

    raw_df.to_csv(
        firms_file,
        index=False,
    )

    print(
        f"[ingest_job] Saved raw FIRMS data: "
        f"{len(raw_df)} rows"
    )

    # --------------------------------------------------------
    # 2. Landcover
    # --------------------------------------------------------

    run_module(
        "src.ingestion.sample_landcover"
    )

    landcover_file = (
        DATA_INTERIM
        / "hotspots_with_landcover.csv"
    )

    if not landcover_file.exists():

        raise FileNotFoundError(
            "Landcover output was not created:\n"
            f"{landcover_file}"
        )

    print(
        f"[ingest_job] Landcover file ready: "
        f"{landcover_file}"
    )

    # --------------------------------------------------------
    # 3. Spatial features
    # --------------------------------------------------------

    run_module(
        "src.features.spatial_join"
    )

    spatial_file = (
        DATA_INTERIM
        / "hotspots_with_spatial_features.csv"
    )

    if not spatial_file.exists():

        raise FileNotFoundError(
            "Spatial feature output was not created:\n"
            f"{spatial_file}"
        )

    print(
        f"[ingest_job] Spatial feature file ready: "
        f"{spatial_file}"
    )

    # --------------------------------------------------------
    # 4. Temporal features
    # --------------------------------------------------------

    run_module(
        "src.features.temporal_features"
    )

    temporal_file = (
        DATA_INTERIM
        / "hotspots_with_temporal_features.csv"
    )

    if not temporal_file.exists():

        raise FileNotFoundError(
            "Temporal feature output was not created:\n"
            f"{temporal_file}"
        )

    print(
        f"[ingest_job] Temporal feature file ready: "
        f"{temporal_file}"
    )

    # --------------------------------------------------------
    # 5. Clustering
    # --------------------------------------------------------

    run_module(
        "src.features.clustering"
    )

    cluster_file = (
        DATA_INTERIM
        / "hotspots_with_cluster_features.csv"
    )

    if not cluster_file.exists():

        raise FileNotFoundError(
            "Cluster feature output was not created:\n"
            f"{cluster_file}"
        )

    print(
        f"[ingest_job] Cluster feature file ready: "
        f"{cluster_file}"
    )

    # --------------------------------------------------------
    # 6. Load final engineered dataset
    # --------------------------------------------------------

    import pandas as pd

    features_df = pd.read_csv(
        cluster_file
    )

    if features_df.empty:

        raise ValueError(
            "Final engineered feature dataset is empty."
        )

    print(
        f"[ingest_job] Final engineered features: "
        f"{len(features_df)} rows"
    )

    return features_df


# ============================================================
# ONE INGESTION CYCLE
# ============================================================

def run_ingest_cycle():
    """
    One complete production cycle:

        FIRMS
          ↓
        Feature Engineering
          ↓
        XGBoost Prediction
          ↓
        PostGIS
    """

    print()
    print("=" * 60)
    print("[ingest_job] Starting ingestion cycle")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Fetch latest FIRMS
    # --------------------------------------------------------

    print(
        "[ingest_job] Fetching latest FIRMS data..."
    )

    raw_df = fetch_all_sensors(
        day_range=1
    )

    if raw_df is None or raw_df.empty:

        print(
            "[ingest_job] No FIRMS hotspots found."
        )

        return

    print(
        f"[ingest_job] FIRMS rows received: "
        f"{len(raw_df)}"
    )

    # --------------------------------------------------------
    # 2. Feature engineering
    # --------------------------------------------------------

    features_df = (
        run_production_feature_pipeline(
            raw_df
        )
    )

    if features_df.empty:

        print(
            "[ingest_job] No engineered features generated."
        )

        return

    # --------------------------------------------------------
    # 3. Load trained model
    # --------------------------------------------------------

    print(
        "[ingest_job] Loading trained model..."
    )

    bundle = load_model()

    # --------------------------------------------------------
    # 4. Prediction
    # --------------------------------------------------------

    print(
        "[ingest_job] Running XGBoost prediction..."
    )

    classified_df = predict(
        features_df,
        bundle,
    )

    if classified_df.empty:

        print(
            "[ingest_job] No predictions generated."
        )

        return

    print(
        f"[ingest_job] Classified rows: "
        f"{len(classified_df)}"
    )

    print(
        "[ingest_job] Prediction distribution:"
    )

    print(
        classified_df[
            "predicted_class"
        ].value_counts()
    )

    # --------------------------------------------------------
    # 5. Store in PostGIS
    # --------------------------------------------------------

    print(
        "[ingest_job] Storing results in PostGIS..."
    )

    db = SessionLocal()

    try:

        for _, row in classified_df.iterrows():

            # -----------------------------------------------
            # Geometry
            # -----------------------------------------------

            geometry = WKTElement(
                (
                    f"POINT("
                    f"{float(row['longitude'])} "
                    f"{float(row['latitude'])}"
                    f")"
                ),
                srid=4326,
            )

            # -----------------------------------------------
            # Hotspot
            # -----------------------------------------------

            hotspot = Hotspot(

                latitude=float(
                    row["latitude"]
                ),

                longitude=float(
                    row["longitude"]
                ),

                geom=geometry,

                acq_date=row.get(
                    "acq_date"
                ),

                frp=row.get(
                    "frp"
                ),

                brightness=row.get(
                    "brightness"
                ),

                confidence=(
                    str(
                        row.get(
                            "confidence"
                        )
                    )
                    if row.get(
                        "confidence"
                    ) is not None
                    else None
                ),

                sensor=row.get(
                    "sensor"
                ),

                distance_to_facility_m=(
                    row.get(
                        "distance_to_facility_m"
                    )
                ),

                nearest_facility_type=(
                    row.get(
                        "nearest_facility_type"
                    )
                ),

                # Dataset column:
                # landcover_class
                #
                # Database column:
                # lc_class

                lc_class=row.get(
                    "landcover_class"
                ),

                persistence_score=(
                    row.get(
                        "persistence_score"
                    )
                ),

                frp_ratio_to_baseline=(
                    row.get(
                        "frp_ratio_to_baseline"
                    )
                ),

                cluster_size=(
                    row.get(
                        "cluster_size"
                    )
                ),

                predicted_class=(
                    row.get(
                        "predicted_class"
                    )
                ),

                predicted_confidence=(
                    row.get(
                        "predicted_confidence"
                    )
                ),

                is_anomaly=(
                    row.get(
                        "predicted_class"
                    )
                    == "industrial_fire"
                ),
            )

            db.add(hotspot)

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        db.commit()

        print(
            f"[ingest_job] Successfully stored "
            f"{len(classified_df)} hotspots."
        )

    except Exception as exc:

        db.rollback()

        print(
            "[ingest_job] Database error."
        )

        print(
            f"[ingest_job] {exc}"
        )

        raise

    finally:

        db.close()

    print("=" * 60)
    print(
        "[ingest_job] Ingestion cycle completed"
    )
    print("=" * 60)
    print()


# ============================================================
# SCHEDULER
# ============================================================

def start_scheduler():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_ingest_cycle,
        "interval",
        hours=3,
        max_instances=1,
    )

    scheduler.start()

    print(
        "[ingest_job] Scheduler started."
    )

    print(
        "[ingest_job] Next ingestion will run "
        "every 3 hours."
    )

    return scheduler


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    run_ingest_cycle()