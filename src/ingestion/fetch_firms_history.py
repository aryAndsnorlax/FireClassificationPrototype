import requests
import pandas as pd

from io import StringIO
from datetime import datetime, timedelta

from src.utils.config import (
    FIRMS_MAP_KEY,
    INDIA_BBOX,
    DATA_RAW,
)


FIRMS_BASE_URL = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
)


SENSORS = [
    "VIIRS_SNPP_NRT",
    "VIIRS_NOAA20_NRT",
    "MODIS_NRT",
]


# --------------------------------------------------
# Historical period
# --------------------------------------------------

START_DATE = "2026-08-16"
END_DATE = "2026-09-14"

WINDOW_DAYS = 5


# --------------------------------------------------
# Fetch one historical window
# --------------------------------------------------

def fetch_firms_window(
    sensor,
    start_date,
    day_range,
    bbox=INDIA_BBOX,
):
    """
    Fetch FIRMS data for a specific historical
    date window.
    """

    bbox_str = ",".join(
        str(value)
        for value in bbox
    )

    url = (
        f"{FIRMS_BASE_URL}/"
        f"{FIRMS_MAP_KEY}/"
        f"{sensor}/"
        f"{bbox_str}/"
        f"{day_range}/"
        f"{start_date}"
    )

    print()
    print(
        f"Requesting {sensor}: "
        f"{start_date} "
        f"({day_range} days)"
    )

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    df = pd.read_csv(
        StringIO(response.text)
    )

    df["sensor"] = sensor

    print(
        f"Received {len(df)} records"
    )

    return df


# --------------------------------------------------
# Generate historical windows
# --------------------------------------------------

def generate_windows(
    start_date,
    end_date,
    window_days=5,
):
    """
    Generate non-overlapping historical
    date windows.
    """

    start = datetime.strptime(
        start_date,
        "%Y-%m-%d",
    ).date()

    end = datetime.strptime(
        end_date,
        "%Y-%m-%d",
    ).date()

    current = start

    windows = []

    while current <= end:

        remaining_days = (
            end - current
        ).days + 1

        days = min(
            window_days,
            remaining_days,
        )

        windows.append(
            (
                current.strftime("%Y-%m-%d"),
                days,
            )
        )

        current += timedelta(
            days=days
        )

    return windows


# --------------------------------------------------
# Fetch all historical data
# --------------------------------------------------

def fetch_historical_firms():

    if not FIRMS_MAP_KEY:
        raise RuntimeError(
            "FIRMS_MAP_KEY not set."
        )

    windows = generate_windows(
        START_DATE,
        END_DATE,
        WINDOW_DAYS,
    )

    print("=" * 80)
    print("FIRMS HISTORICAL DATA DOWNLOAD")
    print("=" * 80)

    print()
    print(
        f"Date range: "
        f"{START_DATE} → {END_DATE}"
    )

    print(
        f"Number of windows: "
        f"{len(windows)}"
    )

    all_frames = []

    for sensor in SENSORS:

        for start_date, days in windows:

            try:

                df = fetch_firms_window(
                    sensor=sensor,
                    start_date=start_date,
                    day_range=days,
                )

                all_frames.append(df)

            except requests.HTTPError as error:

                print(
                    f"ERROR for {sensor} "
                    f"{start_date}: "
                    f"{error}"
                )

            except Exception as error:

                print(
                    f"Unexpected error for "
                    f"{sensor} "
                    f"{start_date}: "
                    f"{error}"
                )

    if not all_frames:

        raise RuntimeError(
            "No FIRMS data was downloaded."
        )

    history = pd.concat(
        all_frames,
        ignore_index=True,
    )

    # --------------------------------------------------
    # Remove exact duplicates
    # --------------------------------------------------

    before = len(history)

    history = history.drop_duplicates()

    after = len(history)

    print()
    print(
        f"Removed duplicate rows: "
        f"{before - after}"
    )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    output_file = (
        DATA_RAW
        / "firms"
        / "firms_history.csv"
    )

    history.to_csv(
        output_file,
        index=False,
    )

    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)

    print(
        f"Total records: "
        f"{len(history)}"
    )

    print(
        f"Unique dates: "
        f"{history['acq_date'].nunique()}"
    )

    print()
    print(
        history["acq_date"]
        .value_counts()
        .sort_index()
    )

    print()
    print(
        f"Saved to:\n{output_file}"
    )

    return history


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    fetch_historical_firms()