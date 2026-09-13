"""Endpoints for querying classified hotspots as GeoJSON."""
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.db.models import Hotspot

router = APIRouter(prefix="/hotspots", tags=["hotspots"])


@router.get("/")
def list_hotspots(
    fire_class: Optional[str] = Query(None, alias="class"),
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Returns classified hotspots as GeoJSON-style records, filterable by
    class, bounding box, and date range.
    """
    query = db.query(Hotspot)

    if fire_class:
        query = query.filter(Hotspot.predicted_class == fire_class)
    if start_date:
        query = query.filter(Hotspot.acq_date >= start_date)
    if end_date:
        query = query.filter(Hotspot.acq_date <= end_date)
    if None not in (min_lon, min_lat, max_lon, max_lat):
        query = query.filter(
            Hotspot.longitude.between(min_lon, max_lon),
            Hotspot.latitude.between(min_lat, max_lat),
        )

    results = query.limit(5000).all()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [h.longitude, h.latitude]},
                "properties": {
                    "id": h.id,
                    "class": h.predicted_class,
                    "confidence": h.predicted_confidence,
                    "frp": h.frp,
                    "acq_date": h.acq_date.isoformat() if h.acq_date else None,
                    "facility_type": h.nearest_facility_type,
                    "is_anomaly": h.is_anomaly,
                },
            }
            for h in results
        ],
    }
