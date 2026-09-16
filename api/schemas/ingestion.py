"""Pydantic schemas for the ingestion status endpoint."""
from typing import Optional
from pydantic import BaseModel


class IngestionStatusResponse(BaseModel):
    status: str  # "operational" | "update_unavailable" | "running"
    source: str
    last_successful_ingestion: Optional[str] = None
    latest_observation: Optional[str] = None
    records_fetched: int = 0
    records_inserted: int = 0
    duplicates_skipped: int = 0
    total_database_records: int = 0
    last_error: Optional[str] = None
    is_running: bool = False
