import requests
import pandas as pd
import time
import os


# ============================================================
# CONFIGURATION
# ============================================================

FIRMS_FILE = "data/interim/firms_history_india.csv"

DETAILED_OUTPUT = "data/processed/environmental_context.csv"
SUMMARY_OUTPUT = "data/processed/environmental_assessment.csv"

BATCH_SIZE = 50

BEFORE_HOURS = 3
AFTER_HOURS = 3

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# PROCESS ONE BATCH
# ============================================================

def get_batch_environment(batch):

    results = []

    # --------------------------------------------------------
    # Open-Meteo accepts multiple coordinates
    # --------------------------------------------------------

    latitudes = batch["latitude"].tolist()
    longitudes = batch["longitude"].tolist()

    dates = batch["acq_date"].unique()

    # --------------------------------------------------------
    # IMPORTANT:
    # A batch must contain the same date.
    # --------------------------------------------------------

    date = str(dates[0])

    # ========================================================
    # WEATHER
    # ========================================================

    weather_params = {
        "latitude": latitudes,
        "longitude": longitudes,
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
        WEATHER_URL,
        params=weather_params,
        timeout=120
    )

    weather_response.raise_for_status()

    weather_data = weather_response.json()

    # Multiple coordinates return a list
    if isinstance(weather_data, dict):
        weather_data = [weather_data]

    # ========================================================
    # AIR QUALITY
    # ========================================================

    air_params = {
        "latitude": latitudes,
        "longitude": longitudes,
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
        AIR_URL,
        params=air_params,
        timeout=120
    )

    air_response.raise_for_status()

    air_data = air_response.json()

    if isinstance(air_data, dict):
        air_data = [air_data]

    # ========================================================
    # MATCH EACH HOTSPOT
    # ========================================================

    for i, (_, hotspot) in enumerate(batch.iterrows()):

        try:

            weather = weather_data[i]
            air = air_data[i]

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

            environment_df = pd.merge(
                weather_df,
                air_df,
                on="time",
                how="inner"
            )

            # ------------------------------------------------
            # FIRMS detection time
            # ------------------------------------------------

            acq_time = str(
                int(hotspot["acq_time"])
            ).zfill(4)

            hour = int(acq_time[:2])
            minute = int(acq_time[2:])

            detection_time = pd.Timestamp(
                f"{date} {hour:02d}:{minute:02d}"
            )

            # ------------------------------------------------
            # Find nearest environmental hour
            # ------------------------------------------------

            environment_df["time_difference"] = (
                environment_df["time"]
                - detection_time
            ).abs()

            nearest_index = (
                environment_df[
                    "time_difference"
                ].idxmin()
            )

            detection_environment_time = (
                environment_df.loc[
                    nearest_index,
                    "time"
                ]
            )

            # ------------------------------------------------
            # Before / After window
            # ------------------------------------------------

            start_time = (
                detection_environment_time
                - pd.Timedelta(
                    hours=BEFORE_HOURS
                )
            )

            end_time = (
                detection_environment_time
                + pd.Timedelta(
                    hours=AFTER_HOURS
                )
            )

            window_df = environment_df[
                (environment_df["time"] >= start_time)
                &
                (environment_df["time"] <= end_time)
            ].copy()

            # ------------------------------------------------
            # Label periods
            # ------------------------------------------------

            window_df["period"] = "after"

            window_df.loc[
                window_df["time"]
                < detection_environment_time,
                "period"
            ] = "before"

            window_df.loc[
                window_df["time"]
                == detection_environment_time,
                "period"
            ] = "detection"

            # ------------------------------------------------
            # Add FIRMS information
            # ------------------------------------------------

            window_df["hotspot_id"] = hotspot.name

            window_df["latitude"] = float(
                hotspot["latitude"]
            )

            window_df["longitude"] = float(
                hotspot["longitude"]
            )

            window_df["firms_date"] = date

            window_df["firms_time"] = (
                detection_time.strftime("%H:%M")
            )

            window_df["environment_time"] = (
                window_df["time"]
            )

            results.append(window_df)

        except Exception as error:

            print(
                f"Error processing hotspot "
                f"{hotspot.name}: {error}"
            )

    return results


# ============================================================
# CREATE SUMMARY
# ============================================================

def create_summary(detailed_df):

    summaries = []

    for hotspot_id, group in detailed_df.groupby(
        "hotspot_id"
    ):

        before = group[
            group["period"] == "before"
        ]

        detection = group[
            group["period"] == "detection"
        ]

        after = group[
            group["period"] == "after"
        ]

        first = group.iloc[0]

        summary = {
            "hotspot_id": hotspot_id,

            "latitude": first["latitude"],
            "longitude": first["longitude"],

            "firms_date": first["firms_date"],
            "firms_time": first["firms_time"],

            # PM2.5
            "before_pm25":
                before["pm2_5"].mean(),

            "detection_pm25":
                detection["pm2_5"].mean(),

            "after_pm25":
                after["pm2_5"].mean(),

            # PM10
            "before_pm10":
                before["pm10"].mean(),

            "detection_pm10":
                detection["pm10"].mean(),

            "after_pm10":
                after["pm10"].mean(),

            # AQI
            "before_aqi":
                before["european_aqi"].mean(),

            "detection_aqi":
                detection["european_aqi"].mean(),

            "after_aqi":
                after["european_aqi"].mean(),

            # Temperature
            "before_temperature":
                before["temperature_2m"].mean(),

            "detection_temperature":
                detection["temperature_2m"].mean(),

            "after_temperature":
                after["temperature_2m"].mean(),

            # Humidity
            "before_humidity":
                before["relative_humidity_2m"].mean(),

            "detection_humidity":
                detection["relative_humidity_2m"].mean(),

            "after_humidity":
                after["relative_humidity_2m"].mean(),

            # Wind speed
            "before_wind_speed":
                before["wind_speed_10m"].mean(),

            "detection_wind_speed":
                detection["wind_speed_10m"].mean(),

            "after_wind_speed":
                after["wind_speed_10m"].mean(),

            # Wind direction
            "before_wind_direction":
                before["wind_direction_10m"].mean(),

            "detection_wind_direction":
                detection[
                    "wind_direction_10m"
                ].mean(),

            "after_wind_direction":
                after[
                    "wind_direction_10m"
                ].mean(),
        }

        summaries.append(summary)

    return pd.DataFrame(summaries)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n========================================")
    print("   BATCH ENVIRONMENTAL PIPELINE")
    print("========================================")

    df = pd.read_csv(FIRMS_FILE)

    print(
        f"\nTotal hotspots: {len(df)}"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Process each date separately.
    # --------------------------------------------------------

    all_results = []

    dates = sorted(
        df["acq_date"].unique()
    )

    print(
        f"Dates to process: {len(dates)}"
    )

    total_batches = 0

    for date in dates:

        date_df = df[
            df["acq_date"] == date
        ].copy()

        print(
            f"\n========================================"
        )

        print(
            f"Processing date: {date}"
        )

        print(
            f"Hotspots on date: {len(date_df)}"
        )

        # ----------------------------------------------------
        # Split date into batches
        # ----------------------------------------------------

        for start in range(
            0,
            len(date_df),
            BATCH_SIZE
        ):

            batch = date_df.iloc[
                start:start + BATCH_SIZE
            ]

            total_batches += 1

            print(
                f"Batch {total_batches}: "
                f"{start + 1}-"
                f"{min(start + BATCH_SIZE, len(date_df))}"
            )

            try:

                batch_results = (
                    get_batch_environment(
                        batch
                    )
                )

                all_results.extend(
                    batch_results
                )

                print("  ✓ Batch complete")

            except Exception as error:

                print(
                    f"  ✗ Batch failed: "
                    f"{error}"
                )

            time.sleep(0.2)

    # ========================================================
    # COMBINE RESULTS
    # ========================================================

    if not all_results:

        print(
            "\nNo results generated."
        )

        return

    detailed_df = pd.concat(
        all_results,
        ignore_index=True
    )

    # ========================================================
    # SAVE DETAILED DATA
    # ========================================================

    detailed_df.to_csv(
        DETAILED_OUTPUT,
        index=False
    )

    print(
        f"\nDetailed data saved:"
    )

    print(
        DETAILED_OUTPUT
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\nCreating environmental assessment..."
    )

    summary_df = create_summary(
        detailed_df
    )

    summary_df.to_csv(
        SUMMARY_OUTPUT,
        index=False
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n========================================")
    print("       PIPELINE COMPLETE")
    print("========================================")

    print(
        f"\nFIRMS hotspots : {len(df)}"
    )

    print(
        f"Processed      : "
        f"{summary_df['hotspot_id'].nunique()}"
    )

    print(
        f"Detailed rows  : "
        f"{len(detailed_df)}"
    )

    print(
        f"Assessment rows: "
        f"{len(summary_df)}"
    )

    print(
        "\nDetailed:"
    )

    print(
        DETAILED_OUTPUT
    )

    print(
        "\nAssessment:"
    )

    print(
        SUMMARY_OUTPUT
    )

    print(
        "\n========================================"
    )


if __name__ == "__main__":
    main()