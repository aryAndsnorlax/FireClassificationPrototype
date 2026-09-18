import requests
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

FIRMS_FILE = "data/interim/firms_history_india.csv"

BEFORE_HOURS = 3
AFTER_HOURS = 3


# ============================================================
# 1. LOAD ONE FIRMS HOTSPOT
# ============================================================

df = pd.read_csv(FIRMS_FILE)

hotspot = df.iloc[0]

latitude = float(hotspot["latitude"])
longitude = float(hotspot["longitude"])
date = hotspot["acq_date"]

acq_time = str(int(hotspot["acq_time"])).zfill(4)

hour = int(acq_time[:2])
minute = int(acq_time[2:])

detection_time = pd.Timestamp(
    f"{date} {hour:02d}:{minute:02d}"
)


print("\n========================================")
print("         FIRMS HOTSPOT")
print("========================================")

print(f"Latitude       : {latitude}")
print(f"Longitude      : {longitude}")
print(f"Detection date : {date}")
print(f"Detection time : {detection_time.strftime('%H:%M')}")


# ============================================================
# 2. GET WEATHER DATA
# ============================================================

weather_url = "https://archive-api.open-meteo.com/v1/archive"

weather_params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": date,
    "end_date": date,
    "hourly": (
        "temperature_2m,"
        "relative_humidity_2m,"
        "wind_speed_10m,"
        "wind_direction_10m"
    ),
    "timezone": "Asia/Kolkata",
}

weather_response = requests.get(
    weather_url,
    params=weather_params,
    timeout=30
)

weather_response.raise_for_status()

weather_data = weather_response.json()

weather_df = pd.DataFrame(weather_data["hourly"])

weather_df["time"] = pd.to_datetime(weather_df["time"])


# ============================================================
# 3. GET AIR QUALITY DATA
# ============================================================

air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

air_params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": date,
    "end_date": date,
    "hourly": (
        "pm2_5,"
        "pm10,"
        "european_aqi"
    ),
    "timezone": "Asia/Kolkata",
}

air_response = requests.get(
    air_url,
    params=air_params,
    timeout=30
)

air_response.raise_for_status()

air_data = air_response.json()

air_df = pd.DataFrame(air_data["hourly"])

air_df["time"] = pd.to_datetime(air_df["time"])


# ============================================================
# 4. COMBINE WEATHER + AIR QUALITY
# ============================================================

environment_df = pd.merge(
    weather_df,
    air_df,
    on="time",
    how="inner"
)


# ============================================================
# 5. FIND NEAREST HOURLY OBSERVATION
# ============================================================

environment_df["time_difference"] = (
    environment_df["time"] - detection_time
).abs()

nearest_index = environment_df["time_difference"].idxmin()

nearest_time = environment_df.loc[nearest_index, "time"]


print("\n========================================")
print("       DETECTION TIME MATCH")
print("========================================")

print(f"FIRMS time        : {detection_time.strftime('%H:%M')}")
print(f"Nearest API time  : {nearest_time.strftime('%H:%M')}")
print(
    f"Difference        : "
    f"{environment_df.loc[nearest_index, 'time_difference']}"
)


# ============================================================
# 6. CREATE BEFORE / DETECTION / AFTER WINDOW
# ============================================================

start_time = nearest_time - pd.Timedelta(hours=BEFORE_HOURS)

end_time = nearest_time + pd.Timedelta(hours=AFTER_HOURS)

window_df = environment_df[
    (environment_df["time"] >= start_time)
    & (environment_df["time"] <= end_time)
].copy()


# ============================================================
# 7. LABEL EACH RECORD
# ============================================================

def classify_period(time):
    if time < nearest_time:
        return "before"

    elif time == nearest_time:
        return "detection"

    else:
        return "after"


window_df["period"] = window_df["time"].apply(
    classify_period
)


# ============================================================
# 8. DISPLAY ENVIRONMENTAL CONTEXT
# ============================================================

columns_to_show = [
    "time",
    "period",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "pm2_5",
    "pm10",
    "european_aqi",
]

print("\n========================================")
print("     ENVIRONMENTAL CONTEXT")
print("========================================")

print(
    window_df[columns_to_show].to_string(
        index=False
    )
)


# ============================================================
# 9. CALCULATE BEFORE / AFTER AVERAGES
# ============================================================

before_df = window_df[
    window_df["period"] == "before"
]

detection_df = window_df[
    window_df["period"] == "detection"
]

after_df = window_df[
    window_df["period"] == "after"
]


print("\n========================================")
print("       BEFORE / AFTER SUMMARY")
print("========================================")


def average(df, column):
    if df.empty:
        return None

    return df[column].mean()


variables = {
    "PM2.5": "pm2_5",
    "PM10": "pm10",
    "AQI": "european_aqi",
    "Temperature": "temperature_2m",
    "Humidity": "relative_humidity_2m",
    "Wind Speed": "wind_speed_10m",
}


for name, column in variables.items():

    before_value = average(before_df, column)
    detection_value = average(detection_df, column)
    after_value = average(after_df, column)

    print(f"\n{name}")

    print(f"  Before    : {before_value}")
    print(f"  Detection : {detection_value}")
    print(f"  After     : {after_value}")


print("\n========================================")
print("              COMPLETE")
print("========================================")