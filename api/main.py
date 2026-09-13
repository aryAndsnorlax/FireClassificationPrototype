"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import hotspots, alerts
from api.scheduler.ingest_job import start_scheduler

app = FastAPI(
    title="Industrial Fire Detection API",
    description="Classified NASA FIRMS hotspots over India — industrial fires, "
                 "persistent thermal sources, agricultural burning, and wildfires.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hotspots.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    # Comment out during local dev if you don't want the scheduler firing
    # start_scheduler()
    pass
