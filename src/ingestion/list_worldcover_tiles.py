import math
import pandas as pd

df = pd.read_csv("data/interim/firms_india.csv")

tiles = set()

for _, row in df.iterrows():
    lat = float(row["latitude"])
    lon = float(row["longitude"])

    lat0 = math.floor(lat / 3) * 3
    lon0 = math.floor(lon / 3) * 3

    lat_prefix = "N" if lat0 >= 0 else "S"
    lon_prefix = "E" if lon0 >= 0 else "W"

    tile = (
        f"{lat_prefix}{abs(lat0):02d}"
        f"{lon_prefix}{abs(lon0):03d}"
    )

    tiles.add(tile)

print("WorldCover tiles required:")
for tile in sorted(tiles):
    print(tile)

print(f"\nTotal tiles: {len(tiles)}")