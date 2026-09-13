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


def nearest_distance(points_gdf: gpd.GeoDataFrame, targets_gdf: gpd.GeoDataFrame,
                      target_id_col: str) -> pd.DataFrame:
    """
    For each point, find the nearest feature in targets_gdf.
    Returns a DataFrame with distance_m and the matched target's id column.
    Reprojects to a metric CRS (EPSG:3857) before measuring distance.
    """
    points_m = points_gdf.to_crs("EPSG:3857")
    targets_m = targets_gdf.to_crs("EPSG:3857")
    joined = gpd.sjoin_nearest(
        points_m, targets_m[[target_id_col, "geometry"]],
        distance_col="distance_m", how="left",
    )
    return joined[[target_id_col, "distance_m"]].reset_index(drop=True)


def label_land_cover(points_gdf: gpd.GeoDataFrame, landcover_gdf: gpd.GeoDataFrame,
                      class_col: str = "lc_class") -> pd.Series:
    """Spatial join each point to the land cover polygon/pixel it falls within."""
    joined = gpd.sjoin(points_gdf, landcover_gdf[[class_col, "geometry"]], how="left")
    return joined[class_col]
