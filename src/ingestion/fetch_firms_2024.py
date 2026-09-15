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
    "VIIRS_SNPP_SP",
    "VIIRS_NOAA20_SP",
    "MODIS_SP",
]


# --------------------------------------------------
# Historical overlap period with FSI
# --------------------------------------------------

START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

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
# Generate non-overlapping windows
# --------------------------------------------------

def generate_windows(
    start_date,
    end_date,
    window_days=5,
):

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
# Fetch historical FIRMS data
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
    print("FIRMS 2024 HISTORICAL DATA DOWNLOAD")
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

    # --------------------------------------------------
    # Output file
    # --------------------------------------------------

    output_file = (
        DATA_RAW
        / "firms"
        / "firms_history_2024.csv"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Start fresh
    if output_file.exists():
        output_file.unlink()

    first_write = True
    total_records = 0

    # --------------------------------------------------
    # Download sensor by sensor / window by window
    # --------------------------------------------------

    for sensor in SENSORS:

        for start_date, days in windows:

            try:

                df = fetch_firms_window(
                    sensor=sensor,
                    start_date=start_date,
                    day_range=days,
                )

                if df.empty:
                    continue

                # ------------------------------------------
                # Validate date
                # ------------------------------------------

                df["acq_date"] = pd.to_datetime(
                    df["acq_date"],
                    errors="coerce"
                )

                invalid_dates = (
                    df["acq_date"].isna().sum()
                )

                if invalid_dates:

                    print(
                        f"WARNING: {invalid_dates} "
                        f"invalid dates in "
                        f"{sensor} {start_date}"
                    )

                    df = df.dropna(
                        subset=["acq_date"]
                    )

                if df.empty:
                    continue

                # ------------------------------------------
                # Keep only requested date range
                # ------------------------------------------

                start = pd.Timestamp(
                    START_DATE
                )

                end = pd.Timestamp(
                    END_DATE
                )

                df = df[
                    (df["acq_date"] >= start)
                    &
                    (df["acq_date"] <= end)
                ]

                if df.empty:
                    continue

                # ------------------------------------------
                # Remove exact duplicates within chunk
                # ------------------------------------------

                before = len(df)

                df = df.drop_duplicates()

                removed = before - len(df)

                if removed:
                    print(
                        f"Removed {removed:,} "
                        f"duplicates from chunk"
                    )

                # ------------------------------------------
                # Append directly to CSV
                # ------------------------------------------

                df.to_csv(
                    output_file,
                    mode="w" if first_write else "a",
                    header=first_write,
                    index=False,
                )

                first_write = False

                total_records += len(df)

                print(
                    f"Written to disk: "
                    f"{len(df):,} records"
                )

                # Free memory
                del df

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

    # --------------------------------------------------
    # Final validation
    # --------------------------------------------------

    if first_write:
        raise RuntimeError(
            "No FIRMS data was downloaded."
        )

    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)

    print(
        f"Records written: "
        f"{total_records:,}"
    )

    print(
        f"Saved to:\n{output_file}"
    )

    # --------------------------------------------------
    # Read final CSV in chunks for validation
    # --------------------------------------------------

    print()
    print("Validating saved dataset...")

    date_min = None
    date_max = None
    unique_dates = set()
    sensor_counts = {}
    row_count = 0

    for chunk in pd.read_csv(
        output_file,
        chunksize=50_000,
        low_memory=False,
    ):

        row_count += len(chunk)

        chunk["acq_date"] = pd.to_datetime(
            chunk["acq_date"],
            errors="coerce"
        )

        chunk_min = chunk["acq_date"].min()
        chunk_max = chunk["acq_date"].max()

        if date_min is None or chunk_min < date_min:
            date_min = chunk_min

        if date_max is None or chunk_max > date_max:
            date_max = chunk_max

        unique_dates.update(
            chunk["acq_date"]
            .dt.strftime("%Y-%m-%d")
            .dropna()
            .unique()
        )

        counts = chunk["sensor"].value_counts()

        for sensor_name, count in counts.items():

            sensor_counts[sensor_name] = (
                sensor_counts.get(sensor_name, 0)
                + int(count)
            )

    print()
    print("========== FINAL FIRMS 2024 DATASET ==========")

    print(
        f"Total records : {row_count:,}"
    )

    print(
        f"Date range    : "
        f"{date_min.date()} → {date_max.date()}"
    )

    print(
        f"Unique dates  : "
        f"{len(unique_dates)}"
    )

    print()
    print("Records by sensor:")

    for sensor_name, count in sorted(
        sensor_counts.items()
    ):
        print(
            f"{sensor_name}: {count:,}"
        )

    print()
    print(
        f"Saved to:\n{output_file}"
    )

    return output_file

# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    fetch_historical_firms()