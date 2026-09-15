import requests
import pandas as pd
from pathlib import Path

from src.utils.config import DATA_RAW


FIRMS_FILE = DATA_RAW / "firms" / "firms_history.csv"
OUTPUT_DIR = DATA_RAW / "landcover"

BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    "/v200/2021/map"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_tile_name(lat, lon):
    """Return the ESA WorldCover 3-degree tile containing a coordinate."""

    lat_tile = int(abs(lat) // 3) * 3
    lon_tile = int(abs(lon) // 3) * 3

    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"

    return f"{lat_prefix}{lat_tile:02d}{lon_prefix}{lon_tile:03d}"


def get_required_tiles():
    """Find all WorldCover tiles required by FIRMS hotspots."""

    df = pd.read_csv(FIRMS_FILE)

    tiles = {
        get_tile_name(row.latitude, row.longitude)
        for row in df.itertuples()
    }

    return sorted(tiles)


def download_tile(tile):
    """Download one WorldCover tile if it does not already exist."""

    filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"Already exists: {tile}")
        return True

    url = f"{BASE_URL}/{filename}"

    print(f"Downloading: {tile}")

    try:
        response = requests.get(
            url,
            stream=True,
            timeout=180,
        )

        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    f.write(chunk)

        print(f"Saved: {tile}")
        return True

    except requests.RequestException as error:
        print(f"FAILED: {tile} -> {error}")

        if output_path.exists():
            output_path.unlink()

        return False


def main():

    if not FIRMS_FILE.exists():
        raise FileNotFoundError(
            f"FIRMS file not found: {FIRMS_FILE}"
        )

    tiles = get_required_tiles()

    print("=" * 70)
    print("ESA WORLDCOVER TILE DOWNLOAD")
    print("=" * 70)
    print(f"Required tiles: {len(tiles)}")
    print()

    successful = 0
    failed = []

    for tile in tiles:

        if download_tile(tile):
            successful += 1
        else:
            failed.append(tile)

    print()
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Required:   {len(tiles)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {len(failed)}")

    if failed:
        print()
        print("Failed tiles:")
        for tile in failed:
            print(f"  {tile}")

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()