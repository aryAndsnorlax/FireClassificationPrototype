from pathlib import Path

import geopandas as gpd
import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "firms"
    / "firms_history_2024.csv"
)

BOUNDARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "india_boundary.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "firms_india_2024.csv"
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

CHUNK_SIZE = 100_000


# --------------------------------------------------
# Filter FIRMS points inside India
# --------------------------------------------------

def filter_firms_india():

    print("=" * 80)
    print("FIRMS 2024 → INDIA FILTER")
    print("=" * 80)

    print(f"Input file    : {INPUT_FILE}")
    print(f"Boundary file : {BOUNDARY_FILE}")
    print(f"Output file   : {OUTPUT_FILE}")
    print()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"FIRMS input file not found:\n{INPUT_FILE}"
        )

    if not BOUNDARY_FILE.exists():
        raise FileNotFoundError(
            f"India boundary file not found:\n{BOUNDARY_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Remove previous incomplete output
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    # --------------------------------------------------
    # Load India boundary
    # --------------------------------------------------

    print("Loading India boundary...")

    india = gpd.read_file(BOUNDARY_FILE)

    if india.empty:
        raise RuntimeError(
            "India boundary GeoJSON is empty."
        )

    # Ensure WGS84
    if india.crs is None:
        india = india.set_crs("EPSG:4326")

    india = india.to_crs("EPSG:4326")

    india_geometry = india.geometry.union_all()

    print("India boundary loaded.")
    print()

    # --------------------------------------------------
    # Process FIRMS in chunks
    # --------------------------------------------------

    first_write = True

    total_rows = 0
    india_rows = 0

    min_date = None
    max_date = None

    print("Processing FIRMS data...")
    print()

    for chunk_number, chunk in enumerate(
        pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE),
        start=1
    ):

        total_rows += len(chunk)

        # Check required columns
        required_columns = {
            "latitude",
            "longitude",
            "acq_date"
        }

        missing = required_columns - set(chunk.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        # --------------------------------------------------
        # Remove invalid coordinates
        # --------------------------------------------------

        chunk["latitude"] = pd.to_numeric(
            chunk["latitude"],
            errors="coerce"
        )

        chunk["longitude"] = pd.to_numeric(
            chunk["longitude"],
            errors="coerce"
        )

        valid_coordinates = (
            chunk["latitude"].between(-90, 90)
            & chunk["longitude"].between(-180, 180)
        )

        chunk = chunk[valid_coordinates].copy()

        if chunk.empty:
            continue

        # --------------------------------------------------
        # Convert to GeoDataFrame
        # --------------------------------------------------

        points = gpd.GeoDataFrame(
            chunk,
            geometry=gpd.points_from_xy(
                chunk["longitude"],
                chunk["latitude"]
            ),
            crs="EPSG:4326"
        )

        # --------------------------------------------------
        # India spatial filter
        # --------------------------------------------------

        inside = points.geometry.intersects(
            india_geometry
        )

        points = points[inside].copy()

        if points.empty:
            continue

        # Remove geometry before CSV
        points = pd.DataFrame(
            points.drop(columns="geometry")
        )

        india_rows += len(points)

        # --------------------------------------------------
        # Track date range
        # --------------------------------------------------

        dates = pd.to_datetime(
            points["acq_date"],
            errors="coerce"
        )

        chunk_min = dates.min()
        chunk_max = dates.max()

        if pd.notna(chunk_min):
            if min_date is None or chunk_min < min_date:
                min_date = chunk_min

        if pd.notna(chunk_max):
            if max_date is None or chunk_max > max_date:
                max_date = chunk_max

        # --------------------------------------------------
        # Append to output
        # --------------------------------------------------

        points.to_csv(
            OUTPUT_FILE,
            mode="w" if first_write else "a",
            header=first_write,
            index=False
        )

        first_write = False

        print(
            f"Chunk {chunk_number:>3} | "
            f"Input: {total_rows:>9,} | "
            f"India: {india_rows:>9,}"
        )

    # --------------------------------------------------
    # Final validation
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("FILTER COMPLETE")
    print("=" * 80)

    print(f"Original records : {total_rows:,}")
    print(f"India records    : {india_rows:,}")

    if total_rows > 0:
        percentage = (
            india_rows / total_rows
        ) * 100

        print(
            f"India percentage : {percentage:.2f}%"
        )

    print(
        f"Date range       : "
        f"{min_date.date() if min_date is not None else 'N/A'}"
        f" → "
        f"{max_date.date() if max_date is not None else 'N/A'}"
    )

    print()
    print(f"Saved to:")
    print(OUTPUT_FILE)

    return OUTPUT_FILE


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    filter_firms_india()