"""
Load land cover data for India (Bhuvan LULC or ESA WorldCover).

NOTE: Bhuvan LULC typically requires manual download from bhuvan.nrsc.gov.in
(no public REST API for bulk programmatic access at time of writing).
ESA WorldCover can be pulled via Microsoft Planetary Computer / AWS S3.

This module assumes the raw raster/vector file has already been placed in
data/raw/landcover/ and provides a loader + simplifier used by the feature
pipeline.
"""
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

from src.utils.config import DATA_RAW, DATA_INTERIM


def load_landcover_raster(path: str) -> gpd.GeoDataFrame:
    """
    Convert a land cover raster (e.g. ESA WorldCover .tif) into vector polygons
    with a class label, for use in spatial joins against FIRMS hotspots.
    """
    with rasterio.open(path) as src:
        image = src.read(1)
        transform = src.transform
        crs = src.crs

        results = [
            {"lc_class": int(value), "geometry": shape(geom)}
            for geom, value in shapes(image, transform=transform)
            if value != src.nodata
        ]

    return gpd.GeoDataFrame(results, crs=crs)


def simplify_classes(gdf: gpd.GeoDataFrame, class_map: dict) -> gpd.GeoDataFrame:
    """
    Map raw land cover class codes to simplified categories used by the
    classifier: {'cropland', 'forest', 'industrial', 'water', 'urban', 'other'}
    """
    gdf = gdf.copy()
    gdf["lc_class"] = gdf["lc_class"].map(class_map).fillna("other")
    return gdf


if __name__ == "__main__":
    # Example usage once a raster has been downloaded manually:
    raw_path = DATA_RAW / "landcover" / "worldcover_india.tif"
    if raw_path.exists():
        gdf = load_landcover_raster(str(raw_path))
        out_path = DATA_INTERIM / "landcover_india.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"Saved land cover polygons to {out_path}")
    else:
        print(f"Place a land cover raster at {raw_path} first (see module docstring).")
