"""SQLAlchemy + GeoAlchemy2 model for the classified hotspots table."""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)

    acq_date = Column(DateTime, nullable=False)
    frp = Column(Float)
    brightness = Column(Float)
    confidence = Column(String)
    sensor = Column(String)

    distance_to_facility_m = Column(Float)
    nearest_facility_type = Column(String)
    lc_class = Column(String)
    persistence_score = Column(Float)
    frp_ratio_to_baseline = Column(Float)
    cluster_size = Column(Integer)

    predicted_class = Column(String, index=True)
    predicted_confidence = Column(Float)
    is_anomaly = Column(Boolean, default=False, index=True)
