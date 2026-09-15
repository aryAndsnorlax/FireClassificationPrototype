import geopandas as gpd
import pandas as pd

from src.utils.geo_utils import df_to_geodataframe, nearest_distance
from src.utils.config import DATA_RAW, DATA_INTERIM


# ============================================================
# Configuration
# ============================================================

FIRMS_FILE = (
    DATA_INTERIM
    / "hotspots_with_landcover_2024.csv"
)

OSM_FILE = (
    DATA_RAW
    / "osm"
    / "osm_industrial_india.geojson"
)

OUTPUT_FILE = (
    DATA_INTERIM
    / "hotspots_with_spatial_features_2024.csv"
)


FACILITY_TYPES = [
    "industrial",
    "plant",
    "quarry",
    "works",
    "factory",
    "mine",
    "brickyard",
    "brickworks",
]


# ============================================================
# Overall nearest facility
# ============================================================

def add_facility_distance(
    hotspots: gpd.GeoDataFrame,
    facilities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    hotspots = hotspots.reset_index(
        drop=True
    ).copy()

    dist_df = nearest_distance(
        hotspots,
        facilities,
        target_id_col="facility_type",
    )

    hotspots[
        "distance_to_facility_m"
    ] = dist_df["distance_m"]

    hotspots[
        "nearest_facility_type"
    ] = dist_df["facility_type"]

    return hotspots


# ============================================================
# Category-wise facility distances
# ============================================================

def add_category_distances(
    hotspots: gpd.GeoDataFrame,
    facilities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    hotspots = hotspots.copy()

    for facility_type in FACILITY_TYPES:

        subset = facilities[
            facilities["facility_type"]
            .astype(str)
            .str.lower()
            == facility_type
        ].copy()

        column_name = (
            f"distance_to_{facility_type}_m"
        )

        if subset.empty:

            hotspots[column_name] = float("nan")

            continue

        dist_df = nearest_distance(
            hotspots,
            subset,
            target_id_col="facility_type",
        )

        hotspots[column_name] = (
            dist_df["distance_m"].values
        )

    return hotspots


# ============================================================
# Main processing
# ============================================================

def run(
    firms_csv: str,
    osm_geojson: str,
) -> gpd.GeoDataFrame:

    print("Loading FIRMS 2024 land-cover dataset...")

    firms_df = pd.read_csv(
        firms_csv,
        low_memory=False
    )

    print(
        f"FIRMS hotspots: {len(firms_df):,}"
    )

    # --------------------------------------------------------
    # Convert FIRMS dataframe to GeoDataFrame
    # --------------------------------------------------------

    hotspots = df_to_geodataframe(
        firms_df
    )

    # --------------------------------------------------------
    # Load OSM facilities
    # --------------------------------------------------------

    print("Loading OSM facilities...")

    facilities = gpd.read_file(
        osm_geojson
    )

    print(
        f"OSM facilities: {len(facilities):,}"
    )

    # --------------------------------------------------------
    # Ensure same CRS
    # --------------------------------------------------------

    facilities = facilities.to_crs(
        "EPSG:4326"
    )

    # --------------------------------------------------------
    # Overall nearest facility
    # --------------------------------------------------------

    print()
    print(
        "Calculating nearest facility..."
    )

    hotspots = add_facility_distance(
        hotspots,
        facilities,
    )

    # --------------------------------------------------------
    # Category-wise distances
    # --------------------------------------------------------

    print(
        "Calculating category distances..."
    )

    hotspots = add_category_distances(
        hotspots,
        facilities,
    )

    return hotspots


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("FIRMS 2024 → OSM SPATIAL FEATURES")
    print("=" * 70)
    print()

    if not FIRMS_FILE.exists():
        raise FileNotFoundError(
            f"FIRMS input file not found:\n{FIRMS_FILE}"
        )

    if not OSM_FILE.exists():
        raise FileNotFoundError(
            f"OSM file not found:\n{OSM_FILE}"
        )

    result = run(
        firms_csv=str(FIRMS_FILE),
        osm_geojson=str(OSM_FILE),
    )

    # --------------------------------------------------------
    # Save without geometry
    # --------------------------------------------------------

    result.drop(
        columns="geometry",
        errors="ignore"
    ).to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 70)
    print("SPATIAL PROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Processed hotspots : {len(result):,}"
    )

    print(
        f"Features created   : {len(result.columns):,}"
    )

    print()
    print("Nearest facility types:")

    print(
        result[
            "nearest_facility_type"
        ].value_counts(
            dropna=False
        ).head(15)
    )

    print()
    print(
        "Distance to nearest facility:"
    )

    print(
        result[
            "distance_to_facility_m"
        ].describe()
    )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)