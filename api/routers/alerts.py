"""Endpoint for the anomaly-only feed — 'possible industrial accident' alerts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.db.models import Hotspot

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
def list_alerts(db: Session = Depends(get_db)):
    """Returns only hotspots flagged is_anomaly=True, most recent first."""
    results = (
        db.query(Hotspot)
        .filter(Hotspot.is_anomaly.is_(True))
        .order_by(Hotspot.acq_date.desc())
        .limit(500)
        .all()
    )
    return [
        {
            "id": h.id,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "class": h.predicted_class,
            "frp": h.frp,
            "frp_ratio_to_baseline": h.frp_ratio_to_baseline,
            "acq_date": h.acq_date.isoformat() if h.acq_date else None,
            "facility_type": h.nearest_facility_type,
        }
        for h in results
    ]
