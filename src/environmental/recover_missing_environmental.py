import os
import time
import requests
import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

FIRMS_FILE = "data/interim/firms_history_india.csv"

ASSESSMENT_FILE = "data/processed/environmental_assessment.csv"
DETAILED_FILE = "data/processed/environmental_context.csv"

CACHE_DIR = "data/interim/environmental_grid_cache"

GRID_SIZE = 0.1
BEFORE_HOURS = 3
AFTER_HOURS = 3

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def make_hotspot_id(index):
    return f"HS_{index:06d}"


def grid_coord(value):
    return round(float(value) / GRID_SIZE) * GRID_SIZE


def request_api(url, params, name, retries=4):

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:

                wait = 30 * (2 ** attempt)

                print(
                    f"      429 from {name}. "
                    f"Waiting {wait}s..."
                )

                time.sleep(wait)
                continue

            print(
                f"      {name} failed: "
                f"HTTP {response.status_code}"
            )

            return None

        except requests.RequestException as e:

            wait = 10 * (attempt + 1)

            print(
                f"      Network error: {e}"
            )

            print(
                f"      Waiting {wait}s..."
            )

            time.sleep(wait)

    return None


# ============================================================
# DOWNLOAD / LOAD GRID
# ============================================================

def get_grid_data(date, lat, lon):

    cache_file = os.path.join(
        CACHE_DIR,
        f"{date}_{lat:.1f}_{lon:.1f}.csv"
    )

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    if os.path.exists(cache_file):

        try:

            cached = pd.read_csv(cache_file)

            if len(cached) > 0:
                return cached

        except Exception:
            pass

    print(
        f"    Downloading "
        f"{lat:.1f}, {lon:.1f} | {date}"
    )

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    weather_params = {

        "latitude": lat,
        "longitude": lon,

        "start_date": date,
        "end_date": date,

        "hourly":
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "wind_direction_10m",

        "timezone": "GMT",

        "wind_speed_unit": "ms",

        "cell_selection": "nearest"
    }

    weather = request_api(
        WEATHER_URL,
        weather_params,
        "weather"
    )

    if weather is None:
        return None

    # --------------------------------------------------------
    # AIR QUALITY
    # --------------------------------------------------------

    air_params = {

        "latitude": lat,
        "longitude": lon,

        "start_date": date,
        "end_date": date,

        "hourly":
            "pm2_5,"
            "pm10,"
            "european_aqi",

        "timezone": "GMT",

        "cell_selection": "nearest"
    }

    air = request_api(
        AIR_URL,
        air_params,
        "air quality"
    )

    if air is None:
        return None

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    weather_df = pd.DataFrame(
        weather["hourly"]
    )

    air_df = pd.DataFrame(
        air["hourly"]
    )

    weather_df["time"] = pd.to_datetime(
        weather_df["time"]
    )

    air_df["time"] = pd.to_datetime(
        air_df["time"]
    )

    df = pd.merge(
        weather_df,
        air_df,
        on="time",
        how="outer"
    )

    df = df.sort_values("time")

    df["grid_lat"] = lat
    df["grid_lon"] = lon

    # Save immediately
    df.to_csv(
        cache_file,
        index=False
    )

    time.sleep(1)

    return df


# ============================================================
# LOAD FIRMS
# ============================================================

print("=" * 60)
print("RECOVERING MISSING ENVIRONMENTAL DATA")
print("=" * 60)

firms = pd.read_csv(FIRMS_FILE)

firms["acq_date"] = pd.to_datetime(
    firms["acq_date"]
).dt.strftime("%Y-%m-%d")

firms["acq_time"] = (
    pd.to_numeric(
        firms["acq_time"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)

# IMPORTANT:
# Same deterministic ID used by original dataset
firms["hotspot_id"] = [
    make_hotspot_id(i)
    for i in firms.index
]

print(
    f"\nTotal FIRMS hotspots: {len(firms)}"
)


# ============================================================
# LOAD EXISTING ASSESSMENT
# ============================================================

existing = pd.read_csv(
    ASSESSMENT_FILE
)

existing["hotspot_id"] = (
    existing["hotspot_id"]
    .astype(str)
)

existing_ids = set(
    existing["hotspot_id"]
)

print(
    f"Already processed: "
    f"{len(existing_ids)}"
)


# ============================================================
# FIND MISSING
# ============================================================

missing = firms[
    ~firms["hotspot_id"].isin(existing_ids)
].copy()

print(
    f"Missing hotspots: "
    f"{len(missing)}"
)

if len(missing) == 0:

    print(
        "\nAll hotspots already processed."
    )

    raise SystemExit


# ============================================================
# GRID
# ============================================================

missing["grid_lat"] = (
    missing["latitude"]
    .apply(grid_coord)
)

missing["grid_lon"] = (
    missing["longitude"]
    .apply(grid_coord)
)

grid_requests = (
    missing[
        [
            "acq_date",
            "grid_lat",
            "grid_lon"
        ]
    ]
    .drop_duplicates()
    .reset_index(drop=True)
)

print(
    f"\nUnique grid/date requests: "
    f"{len(grid_requests)}"
)

print(
    f"Maximum API requests: "
    f"{len(grid_requests) * 2}"
)

print("=" * 60)


# ============================================================
# FETCH GRID DATA
# ============================================================

grid_data = {}

successful = 0
failed = 0

for i, row in grid_requests.iterrows():

    date = row["acq_date"]
    lat = row["grid_lat"]
    lon = row["grid_lon"]

    print(
        f"\n[{i + 1}/{len(grid_requests)}]"
    )

    key = (
        date,
        round(lat, 1),
        round(lon, 1)
    )

    data = get_grid_data(
        date,
        lat,
        lon
    )

    if data is not None:

        grid_data[key] = data
        successful += 1

    else:

        failed += 1

    print(
        f"Progress: "
        f"{successful} successful | "
        f"{failed} failed"
    )


# ============================================================
# BUILD RECORDS
# ============================================================

print("\n")
print("=" * 60)
print("BUILDING RECOVERED RECORDS")
print("=" * 60)

detailed_rows = []
assessment_rows = []

for _, hotspot in missing.iterrows():

    hotspot_id = hotspot["hotspot_id"]

    date = hotspot["acq_date"]

    lat = hotspot["latitude"]
    lon = hotspot["longitude"]

    grid_lat = hotspot["grid_lat"]
    grid_lon = hotspot["grid_lon"]

    key = (
        date,
        round(grid_lat, 1),
        round(grid_lon, 1)
    )

    env = grid_data.get(key)

    if env is None:
        continue

    env = env.copy()

    env["time"] = pd.to_datetime(
        env["time"]
    )

    # --------------------------------------------------------
    # FIRMS TIME
    # --------------------------------------------------------

    acq_time = int(
        hotspot["acq_time"]
    )

    hour = acq_time // 100
    minute = acq_time % 100

    detection_time = pd.Timestamp(
        f"{date} "
        f"{hour:02d}:{minute:02d}"
    )

    # --------------------------------------------------------
    # FIND NEAREST HOURLY RECORD
    # --------------------------------------------------------

    env["time_difference"] = (
        abs(
            env["time"] -
            detection_time
        )
        .dt.total_seconds()
        / 60
    )

    nearest_idx = (
        env["time_difference"]
        .idxmin()
    )

    detection_hour = env.loc[
        nearest_idx,
        "time"
    ]

    # --------------------------------------------------------
    # WINDOW
    # --------------------------------------------------------

    start_time = (
        detection_hour -
        pd.Timedelta(
            hours=BEFORE_HOURS
        )
    )

    end_time = (
        detection_hour +
        pd.Timedelta(
            hours=AFTER_HOURS
        )
    )

    window = env[
        (env["time"] >= start_time) &
        (env["time"] <= end_time)
    ].copy()

    if len(window) == 0:
        continue

    window["period"] = "before"

    window.loc[
        window["time"] == detection_hour,
        "period"
    ] = "detection"

    window.loc[
        window["time"] > detection_hour,
        "period"
    ] = "after"

    # --------------------------------------------------------
    # DETAILED
    # --------------------------------------------------------

    for _, r in window.iterrows():

        detailed_rows.append({

            "time": r["time"],

            "temperature_2m":
                r.get("temperature_2m"),

            "relative_humidity_2m":
                r.get(
                    "relative_humidity_2m"
                ),

            "wind_speed_10m":
                r.get("wind_speed_10m"),

            "wind_direction_10m":
                r.get(
                    "wind_direction_10m"
                ),

            "pm2_5":
                r.get("pm2_5"),

            "pm10":
                r.get("pm10"),

            "european_aqi":
                r.get("european_aqi"),

            "time_difference":
                r.get(
                    "time_difference"
                ),

            "period":
                r["period"],

            "latitude": lat,
            "longitude": lon,

            "firms_date": date,
            "firms_time": acq_time,

            "hotspot_id":
                str(hotspot_id)
        })


    # --------------------------------------------------------
    # HELPER FOR ASSESSMENT
    # --------------------------------------------------------

    def period_mean(column, period):

        values = window.loc[
            window["period"] == period,
            column
        ]

        if len(values) == 0:
            return np.nan

        return values.mean()


    # --------------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------------

    assessment_rows.append({

        "hotspot_id":
            str(hotspot_id),

        "latitude": lat,
        "longitude": lon,

        "firms_date": date,
        "firms_time": acq_time,

        "before_pm25":
            period_mean(
                "pm2_5",
                "before"
            ),

        "detection_pm25":
            period_mean(
                "pm2_5",
                "detection"
            ),

        "after_pm25":
            period_mean(
                "pm2_5",
                "after"
            ),

        "before_pm10":
            period_mean(
                "pm10",
                "before"
            ),

        "detection_pm10":
            period_mean(
                "pm10",
                "detection"
            ),

        "after_pm10":
            period_mean(
                "pm10",
                "after"
            ),

        "before_aqi":
            period_mean(
                "european_aqi",
                "before"
            ),

        "detection_aqi":
            period_mean(
                "european_aqi",
                "detection"
            ),

        "after_aqi":
            period_mean(
                "european_aqi",
                "after"
            ),

        "before_temperature":
            period_mean(
                "temperature_2m",
                "before"
            ),

        "detection_temperature":
            period_mean(
                "temperature_2m",
                "detection"
            ),

        "after_temperature":
            period_mean(
                "temperature_2m",
                "after"
            ),

        "before_humidity":
            period_mean(
                "relative_humidity_2m",
                "before"
            ),

        "detection_humidity":
            period_mean(
                "relative_humidity_2m",
                "detection"
            ),

        "after_humidity":
            period_mean(
                "relative_humidity_2m",
                "after"
            ),

        "before_wind_speed":
            period_mean(
                "wind_speed_10m",
                "before"
            ),

        "detection_wind_speed":
            period_mean(
                "wind_speed_10m",
                "detection"
            ),

        "after_wind_speed":
            period_mean(
                "wind_speed_10m",
                "after"
            ),

        "before_wind_direction":
            period_mean(
                "wind_direction_10m",
                "before"
            ),

        "detection_wind_direction":
            period_mean(
                "wind_direction_10m",
                "detection"
            ),

        "after_wind_direction":
            period_mean(
                "wind_direction_10m",
                "after"
            )
    })


# ============================================================
# DATAFRAMES
# ============================================================

new_detailed = pd.DataFrame(
    detailed_rows
)

new_assessment = pd.DataFrame(
    assessment_rows
)

print(
    f"\nRecovered assessment rows: "
    f"{len(new_assessment)}"
)

print(
    f"Recovered detailed rows: "
    f"{len(new_detailed)}"
)


# ============================================================
# COMBINE
# ============================================================

old_detailed = pd.read_csv(
    DETAILED_FILE
)

old_assessment = pd.read_csv(
    ASSESSMENT_FILE
)

# Ensure IDs have same type
old_detailed["hotspot_id"] = (
    old_detailed["hotspot_id"]
    .astype(str)
)

old_assessment["hotspot_id"] = (
    old_assessment["hotspot_id"]
    .astype(str)
)

new_detailed["hotspot_id"] = (
    new_detailed["hotspot_id"]
    .astype(str)
)

new_assessment["hotspot_id"] = (
    new_assessment["hotspot_id"]
    .astype(str)
)


final_detailed = pd.concat(
    [
        old_detailed,
        new_detailed
    ],
    ignore_index=True
)

final_assessment = pd.concat(
    [
        old_assessment,
        new_assessment
    ],
    ignore_index=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

final_detailed = (
    final_detailed
    .drop_duplicates(
        subset=[
            "hotspot_id",
            "time"
        ]
    )
)

final_assessment = (
    final_assessment
    .drop_duplicates(
        subset=["hotspot_id"]
    )
)


# ============================================================
# SORT SAFELY
# ============================================================

final_assessment["hotspot_id"] = (
    final_assessment["hotspot_id"]
    .astype(str)
)

final_detailed["hotspot_id"] = (
    final_detailed["hotspot_id"]
    .astype(str)
)

final_assessment = (
    final_assessment
    .sort_values("hotspot_id")
)

final_detailed = (
    final_detailed
    .sort_values(
        ["hotspot_id", "time"]
    )
)


# ============================================================
# SAVE
# ============================================================

final_detailed.to_csv(
    DETAILED_FILE,
    index=False
)

final_assessment.to_csv(
    ASSESSMENT_FILE,
    index=False
)


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 60)
print("RECOVERY COMPLETE")
print("=" * 60)

print(
    f"Original FIRMS hotspots : "
    f"{len(firms)}"
)

print(
    f"Final assessment rows   : "
    f"{len(final_assessment)}"
)

print(
    f"Final detailed rows     : "
    f"{len(final_detailed)}"
)

print(
    f"Unique hotspot IDs      : "
    f"{final_assessment['hotspot_id'].nunique()}"
)

print(
    f"\nGrid requests successful: "
    f"{successful}"
)

print(
    f"Grid requests failed    : "
    f"{failed}"
)

print("\nDetailed:")
print(DETAILED_FILE)

print("\nAssessment:")
print(ASSESSMENT_FILE)

print("=" * 60)