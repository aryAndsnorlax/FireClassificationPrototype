"""Shared geopandas/shapely helpers used across the pipeline."""
import geopandas as gpd
import pandas as pd


def df_to_geodataframe(df: pd.DataFrame, lat_col: str = "latitude",
                        lon_col: str = "longitude", crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Convert a plain DataFrame with lat/lon columns into a GeoDataFrame."""
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs=crs,
    )


def nearest_distance(
    points_gdf: gpd.GeoDataFrame,
    targets_gdf: gpd.GeoDataFrame,
    target_id_col: str,
) -> pd.DataFrame:
    """
    For each point, find the nearest feature in targets_gdf.

    Returns exactly one row per input point.
    Distance is measured in meters using EPSG:3857.
    """

    points_m = points_gdf.to_crs("EPSG:3857")
    targets_m = targets_gdf.to_crs("EPSG:3857")

    joined = gpd.sjoin_nearest(
        points_m,
        targets_m[[target_id_col, "geometry"]],
        distance_col="distance_m",
        how="left",
    )

    # sjoin_nearest can return multiple rows when two targets
    # are equally close to the same point.
    # Keep only the first match for each original hotspot.
    joined = joined.reset_index()

    joined = joined.drop_duplicates(
        subset="index",
        keep="first",
    )

    joined = joined.sort_values("index")

    return joined[
        [target_id_col, "distance_m"]
    ].reset_index(drop=True)

def label_land_cover(points_gdf: gpd.GeoDataFrame, landcover_gdf: gpd.GeoDataFrame,
                      class_col: str = "lc_class") -> pd.Series:
    """Spatial join each point to the land cover polygon/pixel it falls within."""
    joined = gpd.sjoin(points_gdf, landcover_gdf[[class_col, "geometry"]], how="left")
    return joined[class_col]
