"""
Spatial indexing using R-tree for fast polygon lookups.
"""

import geopandas as gpd
from shapely.geometry import Point
from typing import List, Tuple, Optional
import logging

try:
    from rtree import index
    RTREE_AVAILABLE = True
except ImportError:
    RTREE_AVAILABLE = False
    logging.warning("rtree not available. Spatial queries will be slower.")

logger = logging.getLogger(__name__)


class SpatialIndex:
    """R-tree spatial index for fast polygon lookups."""
    
    def __init__(self, polygons_gdf: gpd.GeoDataFrame):
        """
        Initialize spatial index.
        
        Args:
            polygons_gdf: GeoDataFrame with polygon geometries
        """
        self.polygons_gdf = polygons_gdf
        self.idx = None
        self.use_rtree = RTREE_AVAILABLE
        
        if self.use_rtree:
            self._build_rtree()
        else:
            logger.warning("Using fallback spatial index (slower)")
    
    def _build_rtree(self):
        """Build R-tree spatial index."""
        logger.info("Building R-tree spatial index...")
        
        self.idx = index.Index()
        
        for pos, (idx, row) in enumerate(self.polygons_gdf.iterrows()):
            bounds = row.geometry.bounds  # (minx, miny, maxx, maxy)
            self.idx.insert(pos, bounds, obj=idx)
        
        logger.info(f"R-tree index built with {len(self.polygons_gdf)} polygons")
    
    def query_point(self, lon: float, lat: float) -> List[int]:
        """
        Find candidate polygons that might contain a point.
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            List of polygon indices (row numbers in GeoDataFrame)
        """
        point = Point(lon, lat)
        
        if self.use_rtree and self.idx is not None:
            # Use R-tree for fast bounding box query
            candidates = list(self.idx.intersection((lon, lat, lon, lat), objects=True))
            return [item.object for item in candidates]
        else:
            # Fallback: check all polygons
            return list(range(len(self.polygons_gdf)))
    
    def query_bounds(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float
    ) -> List[int]:
        """
        Find polygons that intersect with a bounding box.
        
        Args:
            min_lon: Minimum longitude
            min_lat: Minimum latitude
            max_lon: Maximum longitude
            max_lat: Maximum latitude
            
        Returns:
            List of polygon indices
        """
        if self.use_rtree and self.idx is not None:
            candidates = list(self.idx.intersection(
                (min_lon, min_lat, max_lon, max_lat),
                objects=True
            ))
            return [item.object for item in candidates]
        else:
            # Fallback: check all polygons
            return list(range(len(self.polygons_gdf)))
    
    def nearest_polygon(
        self,
        lon: float,
        lat: float,
        k: int = 1
    ) -> List[Tuple[int, float]]:
        """
        Find k nearest polygons to a point.
        
        Args:
            lon: Longitude
            lat: Latitude
            k: Number of nearest polygons to return
            
        Returns:
            List of (polygon_index, distance) tuples
        """
        point = Point(lon, lat)
        
        if self.use_rtree and self.idx is not None:
            # Use R-tree nearest neighbor query
            nearest = list(self.idx.nearest((lon, lat, lon, lat), k, objects=True))
            
            # Compute actual distances
            results = []
            for item in nearest:
                poly_idx = item.object
                polygon = self.polygons_gdf.iloc[poly_idx].geometry
                distance = point.distance(polygon)
                results.append((poly_idx, distance))
            
            return sorted(results, key=lambda x: x[1])
        else:
            # Fallback: compute distances to all polygons
            distances = []
            for idx, row in self.polygons_gdf.iterrows():
                distance = point.distance(row.geometry)
                distances.append((idx, distance))
            
            return sorted(distances, key=lambda x: x[1])[:k]
