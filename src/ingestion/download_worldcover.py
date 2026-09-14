import requests
from pathlib import Path

from src.utils.config import DATA_RAW


TILES = [
    "N06E075",
    "N09E075",
    "N09E078",
    "N12E078",
    "N15E075",
    "N18E081",
    "N18E084",
    "N21E081",
    "N21E084",
    "N24E078",
    "N24E081",
    "N30E072",
    "N30E075",
    "N30E078",
]

BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    "/v200/2021/map"
)

OUTPUT_DIR = DATA_RAW / "landcover"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


for tile in TILES:

    filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"

    url = f"{BASE_URL}/{filename}"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"Already exists: {filename}")
        continue

    print(f"Downloading: {tile}")

    response = requests.get(
        url,
        stream=True,
        timeout=120,
    )

    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    print(f"Saved: {output_path}")

print("\nWorldCover download complete.")