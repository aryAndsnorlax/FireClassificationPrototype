import os
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


# ============================================================
# HELPERS
# ============================================================

def grid_coord(value):
    return round(float(value) / GRID_SIZE) * GRID_SIZE


def get_grid_file(date, lat, lon):

    return os.path.join(
        CACHE_DIR,
        f"{date}_{lat:.1f}_{lon:.1f}.csv"
    )


def period_mean(df, column, period):

    values = df.loc[
        df["period"] == period,
        column
    ]

    if len(values) == 0:
        return np.nan

    return values.mean()


# ============================================================
# LOAD FIRMS
# ============================================================

print("=" * 60)
print("REBUILDING ENVIRONMENTAL OUTPUTS")
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

# Original hotspot ID = FIRMS row index
firms["hotspot_id"] = (
    firms.index.astype(str)
)

firms["grid_lat"] = (
    firms["latitude"]
    .apply(grid_coord)
)

firms["grid_lon"] = (
    firms["longitude"]
    .apply(grid_coord)
)

print(
    f"FIRMS hotspots: {len(firms)}"
)


# ============================================================
# BUILD FROM CACHE
# ============================================================

detailed_rows = []
assessment_rows = []

successful_hotspots = 0
missing_cache = 0

for idx, hotspot in firms.iterrows():

    hotspot_id = str(idx)

    date = hotspot["acq_date"]

    lat = float(hotspot["latitude"])
    lon = float(hotspot["longitude"])

    grid_lat = float(hotspot["grid_lat"])
    grid_lon = float(hotspot["grid_lon"])

    cache_file = get_grid_file(
        date,
        grid_lat,
        grid_lon
    )

    # --------------------------------------------------------
    # CHECK CACHE
    # --------------------------------------------------------

    if not os.path.exists(cache_file):

        missing_cache += 1
        continue

    try:

        env = pd.read_csv(
            cache_file
        )

    except Exception:

        missing_cache += 1
        continue

    if len(env) == 0:

        missing_cache += 1
        continue

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    env["time"] = pd.to_datetime(
        env["time"]
    )

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
    # FIND NEAREST HOURLY OBSERVATION
    # --------------------------------------------------------

    env["time_difference"] = (
        abs(
            env["time"] -
            detection_time
        )
        .dt.total_seconds()
        / 60
    )

    detection_idx = (
        env["time_difference"]
        .idxmin()
    )

    detection_hour = env.loc[
        detection_idx,
        "time"
    ]

    # --------------------------------------------------------
    # BEFORE / DETECTION / AFTER
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

        missing_cache += 1
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
    # DETAILED ROWS
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
                r.get("time_difference"),

            "period":
                r["period"],

            "latitude": lat,
            "longitude": lon,

            "firms_date": date,
            "firms_time": acq_time,

            "hotspot_id":
                hotspot_id
        })

    # --------------------------------------------------------
    # ASSESSMENT ROW
    # --------------------------------------------------------

    assessment_rows.append({

        "hotspot_id":
            hotspot_id,

        "latitude": lat,
        "longitude": lon,

        "firms_date": date,
        "firms_time": acq_time,

        "before_pm25":
            period_mean(
                window,
                "pm2_5",
                "before"
            ),

        "detection_pm25":
            period_mean(
                window,
                "pm2_5",
                "detection"
            ),

        "after_pm25":
            period_mean(
                window,
                "pm2_5",
                "after"
            ),

        "before_pm10":
            period_mean(
                window,
                "pm10",
                "before"
            ),

        "detection_pm10":
            period_mean(
                window,
                "pm10",
                "detection"
            ),

        "after_pm10":
            period_mean(
                window,
                "pm10",
                "after"
            ),

        "before_aqi":
            period_mean(
                window,
                "european_aqi",
                "before"
            ),

        "detection_aqi":
            period_mean(
                window,
                "european_aqi",
                "detection"
            ),

        "after_aqi":
            period_mean(
                window,
                "european_aqi",
                "after"
            ),

        "before_temperature":
            period_mean(
                window,
                "temperature_2m",
                "before"
            ),

        "detection_temperature":
            period_mean(
                window,
                "temperature_2m",
                "detection"
            ),

        "after_temperature":
            period_mean(
                window,
                "temperature_2m",
                "after"
            ),

        "before_humidity":
            period_mean(
                window,
                "relative_humidity_2m",
                "before"
            ),

        "detection_humidity":
            period_mean(
                window,
                "relative_humidity_2m",
                "detection"
            ),

        "after_humidity":
            period_mean(
                window,
                "relative_humidity_2m",
                "after"
            ),

        "before_wind_speed":
            period_mean(
                window,
                "wind_speed_10m",
                "before"
            ),

        "detection_wind_speed":
            period_mean(
                window,
                "wind_speed_10m",
                "detection"
            ),

        "after_wind_speed":
            period_mean(
                window,
                "wind_speed_10m",
                "after"
            ),

        "before_wind_direction":
            period_mean(
                window,
                "wind_direction_10m",
                "before"
            ),

        "detection_wind_direction":
            period_mean(
                window,
                "wind_direction_10m",
                "detection"
            ),

        "after_wind_direction":
            period_mean(
                window,
                "wind_direction_10m",
                "after"
            )
    })

    successful_hotspots += 1

    if successful_hotspots % 500 == 0:

        print(
            f"Processed: "
            f"{successful_hotspots}/"
            f"{len(firms)}"
        )


# ============================================================
# CREATE DATAFRAMES
# ============================================================

final_assessment = pd.DataFrame(
    assessment_rows
)

final_detailed = pd.DataFrame(
    detailed_rows
)


# ============================================================
# ENSURE CORRECT TYPES
# ============================================================

final_assessment["hotspot_id"] = (
    final_assessment["hotspot_id"]
    .astype(str)
)

final_detailed["hotspot_id"] = (
    final_detailed["hotspot_id"]
    .astype(str)
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

final_assessment = (
    final_assessment
    .drop_duplicates(
        subset=["hotspot_id"]
    )
)

final_detailed = (
    final_detailed
    .drop_duplicates(
        subset=[
            "hotspot_id",
            "time"
        ]
    )
)


# ============================================================
# SORT
# ============================================================

final_assessment = (
    final_assessment
    .sort_values(
        "hotspot_id",
        key=lambda x:
            pd.to_numeric(
                x,
                errors="coerce"
            )
    )
)

final_detailed = (
    final_detailed
    .sort_values(
        ["hotspot_id", "time"],
        key=lambda x:
            pd.to_numeric(
                x,
                errors="coerce"
            )
            if x.name == "hotspot_id"
            else x
    )
)


# ============================================================
# SAVE
# ============================================================

final_assessment.to_csv(
    ASSESSMENT_FILE,
    index=False
)

final_detailed.to_csv(
    DETAILED_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n")
print("=" * 60)
print("REBUILD COMPLETE")
print("=" * 60)

print(
    f"FIRMS hotspots        : "
    f"{len(firms)}"
)

print(
    f"Assessment rows       : "
    f"{len(final_assessment)}"
)

print(
    f"Detailed rows         : "
    f"{len(final_detailed)}"
)

print(
    f"Unique hotspot IDs    : "
    f"{final_assessment['hotspot_id'].nunique()}"
)

print(
    f"Missing cache/hotspot : "
    f"{missing_cache}"
)

print("=" * 60)