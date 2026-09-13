"""
Pull FIRMS active fire data (VIIRS/MODIS) for the India bounding box.

Docs: https://firms.modaps.eosdis.nasa.gov/api/area/
"""
import requests
import pandas as pd

from src.utils.config import FIRMS_MAP_KEY, INDIA_BBOX, DATA_RAW

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Sensors to pull. VIIRS_SNPP_NRT / VIIRS_NOAA20_NRT / VIIRS_NOAA21_NRT / MODIS_NRT
# For archive (historical) data, replace _NRT with the archive product name per the API docs.
SENSORS = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]


def fetch_firms(sensor: str, bbox: tuple = INDIA_BBOX, day_range: int = 1) -> pd.DataFrame:
    """
    Fetch FIRMS hotspots for a given sensor and bounding box.

    bbox: (min_lon, min_lat, max_lon, max_lat)
    day_range: number of days of data to pull (1-10 for NRT)
    """
    if not FIRMS_MAP_KEY:
        raise RuntimeError("FIRMS_MAP_KEY not set — see .env.example")

    bbox_str = ",".join(str(x) for x in bbox)
    url = f"{FIRMS_BASE_URL}/{FIRMS_MAP_KEY}/{sensor}/{bbox_str}/{day_range}"

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    from io import StringIO
    df = pd.read_csv(StringIO(resp.text))
    df["sensor"] = sensor
    return df


def fetch_all_sensors(bbox: tuple = INDIA_BBOX, day_range: int = 1) -> pd.DataFrame:
    """Fetch and concatenate all configured sensors."""
    frames = [fetch_firms(sensor, bbox, day_range) for sensor in SENSORS]
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    df = fetch_all_sensors()
    out_path = DATA_RAW / "firms" / "firms_latest.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} hotspots to {out_path}")
