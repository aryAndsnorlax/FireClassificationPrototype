from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FSI_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi"
    / "fsi_fire_reference.csv"
)

FIRMS_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "firms_india_2024.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "fsi_firms_matches_2024.csv"
)


# ============================================================
# Configuration
# ============================================================

# We initially search within 5 km.
# This is a candidate-search radius, NOT our final match threshold.
SEARCH_RADIUS_KM = 5.0

# Only same-day observations are considered initially.
DATE_WINDOW_DAYS = 0


# ============================================================
# Load FSI data
# ============================================================

def load_fsi():

    print("Loading FSI data...")

    df = pd.read_csv(
        FSI_FILE,
        low_memory=False
    )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Lat"] = pd.to_numeric(
        df["Lat"],
        errors="coerce"
    )

    df["Lon"] = pd.to_numeric(
        df["Lon"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["Date", "Lat", "Lon"]
    ).copy()

    df = df[
        df["Date"].dt.year == 2024
    ].copy()

    print(f"FSI 2024 records: {len(df):,}")

    return df


# ============================================================
# Load FIRMS data
# ============================================================

def load_firms():

    print("Loading FIRMS data...")

    df = pd.read_csv(
        FIRMS_FILE,
        low_memory=False
    )

    df["acq_date"] = pd.to_datetime(
        df["acq_date"],
        errors="coerce"
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "acq_date",
            "latitude",
            "longitude"
        ]
    ).copy()

    df = df[
        df["acq_date"].dt.year == 2024
    ].copy()

    print(f"FIRMS India 2024 records: {len(df):,}")

    return df


# ============================================================
# Find nearest FIRMS hotspot for each FSI fire
# ============================================================

def match_fsi_to_firms(fsi, firms):

    print()
    print("=" * 70)
    print("BUILDING SPATIAL INDEX")
    print("=" * 70)

    # --------------------------------------------------------
    # Convert FIRMS coordinates to radians
    # --------------------------------------------------------

    firms_coordinates = np.radians(
        firms[
            ["latitude", "longitude"]
        ].to_numpy()
    )

    # --------------------------------------------------------
    # BallTree using haversine distance
    # --------------------------------------------------------

    tree = BallTree(
        firms_coordinates,
        metric="haversine"
    )

    radius_radians = (
        SEARCH_RADIUS_KM / 6371.0088
    )

    print(
        f"Search radius: {SEARCH_RADIUS_KM} km"
    )

    print(
        f"Date window: ±{DATE_WINDOW_DAYS} day"
    )

    print()
    print("Matching FSI points...")

    results = []

    # --------------------------------------------------------
    # Process each FSI record
    # --------------------------------------------------------

    for i, row in enumerate(
        fsi.iterrows(),
        start=1
    ):

        _, fsi_row = row

        fsi_date = fsi_row["Date"].normalize()

        fsi_lat = fsi_row["Lat"]
        fsi_lon = fsi_row["Lon"]

        fsi_point = np.radians(
            [[fsi_lat, fsi_lon]]
        )

        # ----------------------------------------------------
        # Get FIRMS points within radius
        # ----------------------------------------------------

        indices = tree.query_radius(
            fsi_point,
            r=radius_radians
        )[0]

        if len(indices) == 0:

            results.append(
                {
                    "fsi_id": fsi_row["Id"],
                    "fsi_date": fsi_date,
                    "fsi_lat": fsi_lat,
                    "fsi_lon": fsi_lon,
                    "firms_match_found": False,
                    "firms_candidate_count": 0,
                    "nearest_distance_km": np.nan,
                    "firms_date": pd.NaT,
                    "date_difference_days": np.nan,
                }
            )

            continue

        # ----------------------------------------------------
        # Candidate FIRMS records
        # ----------------------------------------------------

        candidates = firms.iloc[indices].copy()

        candidates["date_difference_days"] = (
            candidates["acq_date"].dt.normalize()
            - fsi_date
        ).abs().dt.days

        # ----------------------------------------------------
        # Apply temporal condition
        # ----------------------------------------------------

        candidates = candidates[
            candidates["date_difference_days"]
            <= DATE_WINDOW_DAYS
        ].copy()

        if candidates.empty:

            results.append(
                {
                    "fsi_id": fsi_row["Id"],
                    "fsi_date": fsi_date,
                    "fsi_lat": fsi_lat,
                    "fsi_lon": fsi_lon,
                    "firms_match_found": False,
                    "firms_candidate_count": 0,
                    "nearest_distance_km": np.nan,
                    "firms_date": pd.NaT,
                    "date_difference_days": np.nan,
                }
            )

            continue

        # ----------------------------------------------------
        # Calculate exact geographic distance
        # ----------------------------------------------------

        candidate_coordinates = np.radians(
            candidates[
                ["latitude", "longitude"]
            ].to_numpy()
        )

        fsi_coordinates = np.radians(
            [[fsi_lat, fsi_lon]]
        )

        # Haversine distance
        lat1 = fsi_coordinates[:, 0][:, None]
        lon1 = fsi_coordinates[:, 1][:, None]

        lat2 = candidate_coordinates[:, 0][None, :]
        lon2 = candidate_coordinates[:, 1][None, :]

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat1)
            * np.cos(lat2)
            * np.sin(dlon / 2) ** 2
        )

        distance_km = (
            2
            * 6371.0088
            * np.arcsin(
                np.sqrt(a)
            )
        ).flatten()

        candidates[
            "distance_km"
        ] = distance_km

        # ----------------------------------------------------
        # Select nearest candidate
        # ----------------------------------------------------

        nearest_idx = (
            candidates["distance_km"]
            .idxmin()
        )

        nearest = candidates.loc[
            nearest_idx
        ]

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        result = {
            "fsi_id": fsi_row["Id"],
            "fsi_date": fsi_date,
            "fsi_lat": fsi_lat,
            "fsi_lon": fsi_lon,

            "firms_match_found": True,

            "firms_candidate_count": len(
                candidates
            ),

            "nearest_distance_km": nearest[
                "distance_km"
            ],

            "firms_date": nearest[
                "acq_date"
            ],

            "date_difference_days": nearest[
                "date_difference_days"
            ],

        }

        # ----------------------------------------------------
        # Preserve useful FIRMS attributes
        # ----------------------------------------------------

        useful_columns = [
            "latitude",
            "longitude",
            "instrument",
            "satellite",
            "frp",
            "brightness",
            "bright_t31",
            "confidence",
            "daynight"
        ]

        for column in useful_columns:

            if column in nearest.index:

                result[
                    f"firms_{column}"
                ] = nearest[column]

        results.append(result)

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if i % 1000 == 0:

            print(
                f"Processed FSI records: "
                f"{i:,}/{len(fsi):,}"
            )

    return pd.DataFrame(results)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("FSI ↔ FIRMS 2024 MATCHING")
    print("=" * 70)
    print()

    if not FSI_FILE.exists():
        raise FileNotFoundError(
            f"FSI file not found:\n{FSI_FILE}"
        )

    if not FIRMS_FILE.exists():
        raise FileNotFoundError(
            f"FIRMS file not found:\n{FIRMS_FILE}"
        )

    fsi = load_fsi()

    firms = load_firms()

    matches = match_fsi_to_firms(
        fsi,
        firms
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    matches.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = len(matches)

    matched = matches[
        "firms_match_found"
    ].sum()

    unmatched = total - matched

    print()
    print("=" * 70)
    print("MATCHING COMPLETE")
    print("=" * 70)

    print(
        f"FSI records          : {total:,}"
    )

    print(
        f"Matched with FIRMS    : {matched:,}"
    )

    print(
        f"Unmatched             : {unmatched:,}"
    )

    if total > 0:

        print(
            f"Match percentage      : "
            f"{matched / total * 100:.2f}%"
        )

    if matched > 0:

        distances = matches.loc[
            matches["firms_match_found"],
            "nearest_distance_km"
        ]

        print()
        print("Distance statistics:")

        print(
            f"Minimum              : "
            f"{distances.min():.3f} km"
        )

        print(
            f"Median               : "
            f"{distances.median():.3f} km"
        )

        print(
            f"Mean                 : "
            f"{distances.mean():.3f} km"
        )

        print(
            f"95th percentile      : "
            f"{distances.quantile(0.95):.3f} km"
        )

        print(
            f"Maximum              : "
            f"{distances.max():.3f} km"
        )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()