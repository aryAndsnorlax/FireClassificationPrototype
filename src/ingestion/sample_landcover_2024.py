import pandas as pd
import rasterio

from src.utils.config import DATA_RAW, DATA_INTERIM


# ============================================================
# Files
# ============================================================

FIRMS_FILE = DATA_INTERIM / "firms_india_2024.csv"

OUTPUT_FILE = (
    DATA_INTERIM
    / "hotspots_with_landcover_2024.csv"
)

LANDCOVER_DIR = DATA_RAW / "landcover"


# ============================================================
# ESA WorldCover classes
# ============================================================

WORLD_COVER_CLASSES = {
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse",
    70: "snow_ice",
    80: "water",
    90: "herbaceous_wetland",
    95: "mangroves",
    100: "moss_lichen",
}


# ============================================================
# WorldCover tile
# ============================================================

def get_tile_name(lat, lon):
    """Return the WorldCover tile containing a coordinate."""

    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"

    lat_tile = int(abs(lat) // 3) * 3
    lon_tile = int(abs(lon) // 3) * 3

    return (
        f"{lat_prefix}{lat_tile:02d}"
        f"{lon_prefix}{lon_tile:03d}"
    )


# ============================================================
# Sample landcover
# ============================================================

def sample_landcover():

    print("=" * 70)
    print("FIRMS 2024 → WORLDCOVER")
    print("=" * 70)

    if not FIRMS_FILE.exists():
        raise FileNotFoundError(
            f"FIRMS India 2024 file not found:\n{FIRMS_FILE}"
        )

    df = pd.read_csv(
        FIRMS_FILE,
        low_memory=False
    )

    print(f"Input hotspots: {len(df):,}")
    print()

    landcover_values = []
    landcover_classes = []
    tile_names = []

    # Cache opened raster datasets so that the same
    # WorldCover tile is not opened for every point.
    raster_cache = {}

    missing_tiles = set()

    try:

        for index, row in df.iterrows():

            lat = pd.to_numeric(
                row["latitude"],
                errors="coerce"
            )

            lon = pd.to_numeric(
                row["longitude"],
                errors="coerce"
            )

            # ------------------------------------------------
            # Invalid coordinates
            # ------------------------------------------------

            if pd.isna(lat) or pd.isna(lon):

                landcover_values.append(None)
                landcover_classes.append("unknown")
                tile_names.append("unknown")

                continue

            # ------------------------------------------------
            # Determine WorldCover tile
            # ------------------------------------------------

            tile = get_tile_name(
                lat,
                lon
            )

            filename = (
                f"ESA_WorldCover_10m_2021_v200_"
                f"{tile}_Map.tif"
            )

            raster_path = (
                LANDCOVER_DIR / filename
            )

            tile_names.append(tile)

            # ------------------------------------------------
            # Missing tile
            # ------------------------------------------------

            if not raster_path.exists():

                missing_tiles.add(tile)

                landcover_values.append(None)
                landcover_classes.append("unknown")

                continue

            # ------------------------------------------------
            # Open tile once and cache it
            # ------------------------------------------------

            if tile not in raster_cache:

                raster_cache[tile] = (
                    rasterio.open(raster_path)
                )

            src = raster_cache[tile]

            # ------------------------------------------------
            # Sample coordinate
            # ------------------------------------------------

            value = list(
                src.sample([(lon, lat)])
            )[0][0]

            value = int(value)

            landcover_values.append(
                value
            )

            landcover_classes.append(
                WORLD_COVER_CLASSES.get(
                    value,
                    "unknown"
                )
            )

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            if (index + 1) % 100_000 == 0:

                print(
                    f"Processed: "
                    f"{index + 1:,}/{len(df):,}"
                )

    finally:

        # Close all cached raster files
        for src in raster_cache.values():
            src.close()

    # ========================================================
    # Add features
    # ========================================================

    df["worldcover_value"] = (
        landcover_values
    )

    df["landcover_class"] = (
        landcover_classes
    )

    df["worldcover_tile"] = (
        tile_names
    )

    # ========================================================
    # Save
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # Summary
    # ========================================================

    print()
    print("=" * 70)
    print("LAND-COVER PROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Processed hotspots: {len(df):,}"
    )

    print()
    print("Land-cover distribution:")

    print(
        df["landcover_class"]
        .value_counts(
            dropna=False
        )
    )

    print()

    if missing_tiles:

        print(
            "Missing WorldCover tiles:"
        )

        for tile in sorted(
            missing_tiles
        ):
            print(
                f"  - {tile}"
            )

    else:

        print(
            "Missing WorldCover tiles: 0"
        )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    sample_landcover()