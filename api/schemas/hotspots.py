"""Pydantic models for Hotspot API responses and GeoJSON serialization."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GeoJsonGeometry(BaseModel):
    """GeoJSON Point geometry."""
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJsonProperties(BaseModel):
    """Standardized hotspot properties for GeoJSON feature consumption."""
    id: int
    fire_class: Optional[str] = Field(None, alias="class")
    confidence: Optional[float] = None
    frp: Optional[float] = None
    brightness: Optional[float] = None
    sensor: Optional[str] = None
    acq_date: Optional[str] = None
    facility_type: Optional[str] = None
    distance_to_facility_m: Optional[float] = None
    persistence_score: Optional[float] = None
    frp_ratio_to_baseline: Optional[float] = None
    lc_class: Optional[str] = None
    cluster_size: Optional[int] = None
    is_anomaly: Optional[bool] = False
    risk_score: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class GeoJsonFeature(BaseModel):
    """GeoJSON Feature representation."""
    type: str = "Feature"
    geometry: GeoJsonGeometry
    properties: GeoJsonProperties


class GeoJsonFeatureCollection(BaseModel):
    """RFC 7946 compliant GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: List[GeoJsonFeature]


class HotspotDetailResponse(BaseModel):
    """Full detail view for a specific hotspot."""
    id: int
    latitude: float
    longitude: float
    acq_date: datetime
    frp: Optional[float] = None
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    sensor: Optional[str] = None
    distance_to_facility_m: Optional[float] = None
    nearest_facility_type: Optional[str] = None
    lc_class: Optional[str] = None
    persistence_score: Optional[float] = None
    frp_ratio_to_baseline: Optional[float] = None
    cluster_size: Optional[int] = None
    predicted_class: Optional[str] = None
    predicted_confidence: Optional[float] = None
    is_anomaly: Optional[bool] = False
    risk_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class HotspotStatsResponse(BaseModel):
    """Aggregated dashboard surveillance statistics."""
    total_hotspots: int = 0
    high_risk_count: int = 0
    anomaly_count: int = 0
    class_breakdown: Dict[str, int] = Field(default_factory=dict)
    avg_frp: Optional[float] = None
    latest_acq_date: Optional[str] = None


class AlertItemResponse(BaseModel):
    """Anomaly alert item for the alerts feed."""
    id: int
    latitude: float
    longitude: float
    fire_class: Optional[str] = Field(None, alias="class")
    frp: Optional[float] = None
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    frp_ratio_to_baseline: Optional[float] = None
    acq_date: Optional[str] = None
    facility_type: Optional[str] = None
    risk_score: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
