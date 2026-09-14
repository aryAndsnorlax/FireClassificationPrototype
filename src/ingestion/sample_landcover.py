import pandas as pd
import rasterio

from src.utils.config import DATA_RAW, DATA_INTERIM


FIRMS_FILE = DATA_INTERIM / "firms_india.csv"
OUTPUT_FILE = DATA_INTERIM / "hotspots_with_landcover.csv"

LANDCOVER_DIR = DATA_RAW / "landcover"


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


def get_tile_name(lat, lon):
    """Return the WorldCover tile containing a coordinate."""

    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"

    lat_tile = int(abs(lat) // 3) * 3
    lon_tile = int(abs(lon) // 3) * 3

    return f"{lat_prefix}{lat_tile:02d}{lon_prefix}{lon_tile:03d}"


def sample_landcover():
    df = pd.read_csv(FIRMS_FILE)

    landcover_values = []
    landcover_classes = []
    tile_names = []

    for _, row in df.iterrows():

        lat = row["latitude"]
        lon = row["longitude"]

        tile = get_tile_name(lat, lon)

        filename = (
            f"ESA_WorldCover_10m_2021_v200_"
            f"{tile}_Map.tif"
        )

        raster_path = LANDCOVER_DIR / filename

        if not raster_path.exists():
            print(f"WARNING: Missing tile {tile}")

            landcover_values.append(None)
            landcover_classes.append("unknown")
            tile_names.append(tile)

            continue

        with rasterio.open(raster_path) as src:

            value = list(
                src.sample([(lon, lat)])
            )[0][0]

        value = int(value)

        landcover_values.append(value)

        landcover_classes.append(
            WORLD_COVER_CLASSES.get(value, "unknown")
        )

        tile_names.append(tile)

    df["worldcover_value"] = landcover_values
    df["landcover_class"] = landcover_classes
    df["worldcover_tile"] = tile_names

    df.to_csv(OUTPUT_FILE, index=False)

    print()
    print(f"Processed hotspots: {len(df)}")

    print()
    print("Land-cover distribution:")
    print(df["landcover_class"].value_counts())

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    sample_landcover()