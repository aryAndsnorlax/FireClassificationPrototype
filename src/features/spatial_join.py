"""
Spatial feature engineering: for each FIRMS hotspot, compute
- distance to nearest industrial facility (overall + by facility type)
- land cover class at that location
"""
import geopandas as gpd
import pandas as pd

from src.utils.geo_utils import df_to_geodataframe, nearest_distance, label_land_cover
from src.utils.config import DATA_RAW, DATA_INTERIM


def add_facility_distance(hotspots: gpd.GeoDataFrame, facilities: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Attach distance_to_facility_m and nearest facility_type to each hotspot."""
    dist_df = nearest_distance(hotspots, facilities, target_id_col="facility_type")
    hotspots = hotspots.reset_index(drop=True)
    hotspots["distance_to_facility_m"] = dist_df["distance_m"]
    hotspots["nearest_facility_type"] = dist_df["facility_type"]
    return hotspots


def add_landcover_class(hotspots: gpd.GeoDataFrame, landcover: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Attach land cover class to each hotspot."""
    hotspots = hotspots.copy()
    hotspots["lc_class"] = label_land_cover(hotspots, landcover)
    return hotspots


def run(firms_csv: str, osm_geojson: str, landcover_geojson: str) -> gpd.GeoDataFrame:
    firms_df = pd.read_csv(firms_csv)
    hotspots = df_to_geodataframe(firms_df)

    facilities = gpd.read_file(osm_geojson)
    landcover = gpd.read_file(landcover_geojson)

    hotspots = add_facility_distance(hotspots, facilities)
    hotspots = add_landcover_class(hotspots, landcover)
    return hotspots


if __name__ == "__main__":
    result = run(
        firms_csv=str(DATA_RAW / "firms" / "firms_latest.csv"),
        osm_geojson=str(DATA_RAW / "osm" / "osm_industrial_india.geojson"),
        landcover_geojson=str(DATA_INTERIM / "landcover_india.geojson"),
    )
    out_path = DATA_INTERIM / "hotspots_with_spatial_features.geojson"
    result.to_file(out_path, driver="GeoJSON")
    print(f"Saved {len(result)} enriched hotspots to {out_path}")
