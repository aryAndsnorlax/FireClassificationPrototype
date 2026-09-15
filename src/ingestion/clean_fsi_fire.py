from pathlib import Path

import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "fsi"
    / "fsi_fire_archive.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi"
    / "fsi_fire_reference.csv"
)

BOUNDARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "india_boundary.geojson"
)


# ============================================================
# LOAD RAW FSI DATA
# ============================================================

print("Loading FSI fire archive...")

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print(f"Raw records: {len(df):,}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Id",
    "Date",
    "Sensor",
    "Lon",
    "Lat",
    "State",
    "Year",
    "ACQTIME",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# DATE
# ============================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

invalid_dates = df["Date"].isna().sum()

if invalid_dates:
    raise ValueError(
        f"Invalid dates found: {invalid_dates:,}"
    )


# ============================================================
# COORDINATES
# ============================================================

df["Lon"] = pd.to_numeric(
    df["Lon"],
    errors="coerce"
)

df["Lat"] = pd.to_numeric(
    df["Lat"],
    errors="coerce"
)

invalid_coordinates = (
    df["Lon"].isna()
    | df["Lat"].isna()
    | ~df["Lon"].between(-180, 180)
    | ~df["Lat"].between(-90, 90)
)

invalid_coordinate_count = invalid_coordinates.sum()

if invalid_coordinate_count:
    raise ValueError(
        f"Invalid coordinates found: "
        f"{invalid_coordinate_count:,}"
    )


# ============================================================
# ACTUAL DATE FEATURES
# ============================================================

# IMPORTANT:
# The original FSI "Year" column is inconsistent for some
# records. Therefore Date is treated as authoritative.

df["year"] = df["Date"].dt.year
df["month"] = df["Date"].dt.month
df["day"] = df["Date"].dt.day
df["day_of_year"] = df["Date"].dt.dayofyear


# ============================================================
# EXACT DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates()

duplicates_removed = before - len(df)

print(
    f"Exact duplicates removed: "
    f"{duplicates_removed:,}"
)


# ============================================================
# INDIA BOUNDARY FLAG
# ============================================================

print("Checking India boundary...")

india = gpd.read_file(
    BOUNDARY_FILE
).to_crs("EPSG:4326")


points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["Lon"],
        df["Lat"]
    ),
    crs="EPSG:4326"
)


joined = gpd.sjoin(
    points,
    india[["geometry"]],
    how="left",
    predicate="within"
)


df["inside_india_boundary"] = (
    joined["index_right"].notna().to_numpy()
)


# ============================================================
# IMPORTANT:
# DO NOT DROP OUTSIDE-BOUNDARY RECORDS
# ============================================================

inside_count = int(
    df["inside_india_boundary"].sum()
)

outside_count = len(df) - inside_count


# ============================================================
# DATA QUALITY FLAGS
# ============================================================

# Suspicious geographic envelope.
# These are flagged, NOT removed.

df["suspicious_coordinate"] = (
    (df["Lat"] < 5)
    | (df["Lat"] > 35)
    | (df["Lon"] < 68)
    | (df["Lon"] > 98)
)


# ============================================================
# SENSOR NORMALIZATION
# ============================================================

df["Sensor"] = (
    df["Sensor"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# STATE NORMALIZATION
# ============================================================

df["State"] = (
    df["State"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    by=["Date", "State", "Lat", "Lon"]
).reset_index(drop=True)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("FSI FIRE REFERENCE DATASET")
print("=" * 60)

print(f"Total records           : {len(df):,}")
print(f"Date range              : {df['Date'].min().date()} → {df['Date'].max().date()}")
print(f"Invalid dates           : {invalid_dates:,}")
print(f"Invalid coordinates     : {invalid_coordinate_count:,}")
print(f"Exact duplicates removed: {duplicates_removed:,}")

print()
print(f"Inside India boundary   : {inside_count:,}")
print(f"Outside boundary        : {outside_count:,}")

print(
    f"Inside percentage       : "
    f"{inside_count / len(df) * 100:.2f}%"
)

print(
    f"Outside percentage      : "
    f"{outside_count / len(df) * 100:.2f}%"
)

print()
print("Suspicious coordinate records:")
print(
    int(df["suspicious_coordinate"].sum())
)

print()
print("Sensors:")
print(
    df["Sensor"].value_counts().to_string()
)

print()
print("Records by actual year:")
print(
    df["year"]
    .value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

# GeoDataFrame geometry is not needed in CSV.
df = pd.DataFrame(df).drop(
    columns=["geometry"],
    errors="ignore"
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:")
print(OUTPUT_FILE)