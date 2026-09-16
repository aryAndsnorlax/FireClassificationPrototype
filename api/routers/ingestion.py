

"""Router for satellite data ingestion monitoring and administrative control."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas.ingestion import IngestionStatusResponse
from api.scheduler.ingest_job import get_ingestion_status, run_ingest_cycle

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/status", response_model=IngestionStatusResponse)
def get_status():
    """
    Returns current satellite data ingestion status, last successful update timestamp,
    latest observation timestamp, and database counts.
    """
    return get_ingestion_status()


@router.post("/trigger")
def trigger_ingestion(background_tasks: BackgroundTasks, synchronous: bool = False):
    """
    Manually triggers an incremental satellite ingestion cycle.
    Supports synchronous mode for testing/diagnostics or asynchronous background task.
    """
    current_status = get_ingestion_status()
    if current_status.get("is_running"):
        return {"status": "already_running", "message": "An ingestion cycle is currently in progress."}

    if synchronous:
        try:
            result = run_ingest_cycle(day_range=1)
            return {"status": "completed", "result": result}
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {err}")

    background_tasks.add_task(run_ingest_cycle, day_range=1)
    return {"status": "scheduled", "message": "Satellite data ingestion cycle queued in background."}
