from pathlib import Path

import pandas as pd
import geopandas as gpd


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FSI_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi"
    / "fsi_fire_clean.csv"
)

BOUNDARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "india_boundary.geojson"
)


# --------------------------------------------------
# Load FSI data
# --------------------------------------------------

print("Loading FSI data...")

df = pd.read_csv(
    FSI_FILE,
    low_memory=False
)

print(f"FSI records: {len(df):,}")


# --------------------------------------------------
# Create GeoDataFrame
# --------------------------------------------------

points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["Lon"],
        df["Lat"]
    ),
    crs="EPSG:4326"
)


# --------------------------------------------------
# Load India boundary
# --------------------------------------------------

print("Loading India boundary...")

india = gpd.read_file(
    BOUNDARY_FILE
)

india = india.to_crs("EPSG:4326")


# --------------------------------------------------
# Spatial validation
# --------------------------------------------------

print("Checking points against India boundary...")

inside = gpd.sjoin(
    points,
    india[["geometry"]],
    how="left",
    predicate="within"
)

inside_mask = inside["index_right"].notna()


# --------------------------------------------------
# Results
# --------------------------------------------------

inside_count = inside_mask.sum()
outside_count = (~inside_mask).sum()

print()
print("========== FSI BOUNDARY VALIDATION ==========")

print(f"Total records : {len(df):,}")
print(f"Inside India  : {inside_count:,}")
print(f"Outside India : {outside_count:,}")

print(
    f"Inside percentage : "
    f"{inside_count / len(df) * 100:.2f}%"
)

print(
    f"Outside percentage: "
    f"{outside_count / len(df) * 100:.2f}%"
)


# --------------------------------------------------
# Inspect outside points
# --------------------------------------------------

if outside_count > 0:

    outside = df.loc[
        ~inside_mask
    ].copy()

    print()
    print("Outside points by state:")

    print(
        outside["State"]
        .value_counts()
        .head(20)
        .to_string()
    )

    print()
    print("Sample outside coordinates:")

    print(
        outside[
            ["Date", "State", "Lon", "Lat"]
        ]
        .head(20)
        .to_string(index=False)
    )


print()
print("Validation complete.")