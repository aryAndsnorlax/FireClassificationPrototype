"""
Development database fixtures for testing API and frontend integration.

These fixtures are explicitly tagged with `sensor='VIIRS_DEV_FIXTURE'` so they
can be safely seeded, queried for integration tests, and deleted prior to production.
"""
from datetime import datetime, timezone
from geoalchemy2.elements import WKTElement

from api.db.session import SessionLocal
from api.db.models import Hotspot

DEV_FIXTURE_SENSOR = "VIIRS_DEV_FIXTURE"

DEV_HOTSPOTS = [
    {
        "latitude": 22.4707,
        "longitude": 70.0577,
        "acq_date": datetime(2026, 9, 15, 6, 30, tzinfo=timezone.utc),
        "frp": 142.5,
        "brightness": 372.4,
        "confidence": "high",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 320.0,
        "nearest_facility_type": "Refinery & Petrochemicals Complex",
        "lc_class": "industrial",
        "persistence_score": 0.85,
        "frp_ratio_to_baseline": 3.85,
        "cluster_size": 4,
        "predicted_class": "industrial_fire",
        "predicted_confidence": 0.94,
        "is_anomaly": True,
        "risk_score": 0.95,
    },
    {
        "latitude": 22.8397,
        "longitude": 69.7180,
        "acq_date": datetime(2026, 9, 15, 6, 30, tzinfo=timezone.utc),
        "frp": 78.2,
        "brightness": 341.1,
        "confidence": "nominal",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 450.0,
        "nearest_facility_type": "Ultra Mega Power Plant",
        "lc_class": "industrial",
        "persistence_score": 0.90,
        "frp_ratio_to_baseline": 1.15,
        "cluster_size": 2,
        "predicted_class": "persistent_industrial",
        "predicted_confidence": 0.91,
        "is_anomaly": False,
        "risk_score": 0.88,
    },
    {
        "latitude": 24.1982,
        "longitude": 82.6738,
        "acq_date": datetime(2026, 9, 15, 5, 45, tzinfo=timezone.utc),
        "frp": 65.0,
        "brightness": 335.8,
        "confidence": "nominal",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 620.0,
        "nearest_facility_type": "Super Thermal Power Station",
        "lc_class": "industrial",
        "persistence_score": 0.78,
        "frp_ratio_to_baseline": 1.05,
        "cluster_size": 3,
        "predicted_class": "persistent_industrial",
        "predicted_confidence": 0.89,
        "is_anomaly": False,
        "risk_score": 0.84,
    },
    {
        "latitude": 23.7500,
        "longitude": 86.4200,
        "acq_date": datetime(2026, 9, 15, 5, 0, tzinfo=timezone.utc),
        "frp": 45.3,
        "brightness": 328.0,
        "confidence": "nominal",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 1200.0,
        "nearest_facility_type": "Open Cast Coal Colliery",
        "lc_class": "mine_barren",
        "persistence_score": 0.95,
        "frp_ratio_to_baseline": 1.10,
        "cluster_size": 5,
        "predicted_class": "coal_seam_fire",
        "predicted_confidence": 0.86,
        "is_anomaly": False,
        "risk_score": 0.82,
    },
    {
        "latitude": 30.2458,
        "longitude": 75.8421,
        "acq_date": datetime(2026, 9, 15, 4, 15, tzinfo=timezone.utc),
        "frp": 28.0,
        "brightness": 318.5,
        "confidence": "nominal",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 4800.0,
        "nearest_facility_type": "Grain Storage Silos",
        "lc_class": "cropland",
        "persistence_score": 0.15,
        "frp_ratio_to_baseline": 0.95,
        "cluster_size": 8,
        "predicted_class": "agricultural_burning",
        "predicted_confidence": 0.93,
        "is_anomaly": False,
        "risk_score": 0.45,
    },
    {
        "latitude": 11.6664,
        "longitude": 76.6291,
        "acq_date": datetime(2026, 9, 15, 3, 50, tzinfo=timezone.utc),
        "frp": 54.1,
        "brightness": 331.2,
        "confidence": "high",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 12400.0,
        "nearest_facility_type": "Forest Reserve Outpost",
        "lc_class": "dense_forest",
        "persistence_score": 0.20,
        "frp_ratio_to_baseline": 1.40,
        "cluster_size": 6,
        "predicted_class": "wildfire",
        "predicted_confidence": 0.88,
        "is_anomaly": False,
        "risk_score": 0.72,
    },
    {
        "latitude": 17.6868,
        "longitude": 83.2185,
        "acq_date": datetime(2026, 9, 15, 6, 10, tzinfo=timezone.utc),
        "frp": 115.0,
        "brightness": 365.0,
        "confidence": "high",
        "sensor": DEV_FIXTURE_SENSOR,
        "distance_to_facility_m": 280.0,
        "nearest_facility_type": "Petrochemical Processing Zone",
        "lc_class": "industrial",
        "persistence_score": 0.82,
        "frp_ratio_to_baseline": 3.40,
        "cluster_size": 3,
        "predicted_class": "industrial_fire",
        "predicted_confidence": 0.92,
        "is_anomaly": True,
        "risk_score": 0.93,
    },
]


def seed_fixtures():
    """Seeds the dev fixtures into the database."""
    db = SessionLocal()
    try:
        # Clear existing dev fixtures first to prevent duplicate accumulation
        deleted = (
            db.query(Hotspot)
            .filter(Hotspot.sensor == DEV_FIXTURE_SENSOR)
            .delete(synchronize_session=False)
        )
        if deleted > 0:
            print(f"[seed_dev_fixtures] Removed {deleted} previous dev fixtures.")

        created_hotspots = []
        for d in DEV_HOTSPOTS:
            h = Hotspot(
                latitude=d["latitude"],
                longitude=d["longitude"],
                geom=WKTElement(f"POINT({d['longitude']} {d['latitude']})", srid=4326),
                acq_date=d["acq_date"],
                frp=d["frp"],
                brightness=d["brightness"],
                confidence=d["confidence"],
                sensor=d["sensor"],
                distance_to_facility_m=d["distance_to_facility_m"],
                nearest_facility_type=d["nearest_facility_type"],
                lc_class=d["lc_class"],
                persistence_score=d["persistence_score"],
                frp_ratio_to_baseline=d["frp_ratio_to_baseline"],
                cluster_size=d["cluster_size"],
                predicted_class=d["predicted_class"],
                predicted_confidence=d["predicted_confidence"],
                is_anomaly=d["is_anomaly"],
                risk_score=d["risk_score"],
            )
            db.add(h)
            created_hotspots.append(h)

        db.commit()
        print(f"[seed_dev_fixtures] Successfully seeded {len(created_hotspots)} development fixtures.")
        return len(created_hotspots)
    finally:
        db.close()


def clear_dev_fixtures():
    """Wipes all dev fixtures from the database."""
    db = SessionLocal()
    try:
        deleted = (
            db.query(Hotspot)
            .filter(Hotspot.sensor == DEV_FIXTURE_SENSOR)
            .delete(synchronize_session=False)
        )
        db.commit()
        print(f"[seed_dev_fixtures] Cleared {deleted} development fixtures.")
        return deleted
    finally:
        db.close()


if __name__ == "__main__":
    seed_fixtures()
