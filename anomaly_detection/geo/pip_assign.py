"""
Point-in-polygon assignment with R-tree spatial indexing.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from typing import Dict, Tuple, Optional, List
import logging

from .spatial_index import SpatialIndex

logger = logging.getLogger(__name__)


class PointInPolygonAssigner:
    """Assign points to regions using point-in-polygon testing."""
    
    def __init__(
        self,
        polygons_gdf: gpd.GeoDataFrame,
        metadata_df: pd.DataFrame,
        config: Dict
    ):
        """
        Initialize PIP assigner.
        
        Args:
            polygons_gdf: GeoDataFrame with region polygons
            metadata_df: DataFrame with region metadata
            config: Configuration dictionary
        """
        self.polygons_gdf = polygons_gdf
        self.metadata_df = metadata_df
        self.config = config.get("geo", {}).get("pip", {})
        
        # Build spatial index
        use_rtree = self.config.get("use_rtree", True)
        if use_rtree:
            self.spatial_index = SpatialIndex(polygons_gdf)
        else:
            self.spatial_index = None
        
        # Configuration
        self.fallback_to_nearest = self.config.get("fallback_to_nearest", True)
        self.max_distance_km = self.config.get("max_distance_km", 500)
        
        # Statistics
        self.assignment_stats = {
            'total': 0,
            'contained': 0,
            'nearest_centroid': 0,
            'outside_region': 0,
            'ambiguous': 0
        }
    
    def assign_point(
        self,
        lon: float,
        lat: float,
        cluster_probs: Optional[np.ndarray] = None
    ) -> Tuple[int, str, Dict]:
        """
        Assign a single point to a region.
        
        Args:
            lon: Longitude
            lat: Latitude
            cluster_probs: Cluster probabilities (optional, for ambiguity resolution)
            
        Returns:
            Tuple of (region_id, assignment_method, metadata)
        """
        point = Point(lon, lat)
        
        # Find candidate polygons using spatial index
        if self.spatial_index is not None:
            candidate_indices = self.spatial_index.query_point(lon, lat)
        else:
            candidate_indices = list(range(len(self.polygons_gdf)))
        
        # Test containment for candidates
        containing_regions = []
        for idx in candidate_indices:
            polygon = self.polygons_gdf.iloc[idx].geometry
            if polygon.contains(point):
                region_id = self.polygons_gdf.iloc[idx]['region_id']
                containing_regions.append((region_id, idx))
        
        # Case 1: Point is contained in exactly one region
        if len(containing_regions) == 1:
            region_id = containing_regions[0][0]
            metadata = self._get_region_metadata(region_id)
            self.assignment_stats['contained'] += 1
            return region_id, 'contained', metadata
        
        # Case 2: Point is contained in multiple regions (ambiguous)
        if len(containing_regions) > 1:
            self.assignment_stats['ambiguous'] += 1
            
            # Resolve ambiguity using cluster probabilities
            if cluster_probs is not None:
                region_id = self._resolve_ambiguity_by_prob(
                    containing_regions, cluster_probs
                )
            else:
                # Use nearest centroid
                region_id = self._resolve_ambiguity_by_distance(
                    containing_regions, lon, lat
                )
            
            metadata = self._get_region_metadata(region_id)
            metadata['ambiguous'] = True
            metadata['n_candidates'] = len(containing_regions)
            
            logger.debug(f"Ambiguous point ({lon:.2f}, {lat:.2f}) assigned to region {region_id}")
            
            return region_id, 'ambiguous', metadata
        
        # Case 3: Point is not contained in any region
        if self.fallback_to_nearest:
            region_id, distance_km = self._find_nearest_centroid(lon, lat)
            
            if distance_km <= self.max_distance_km:
                metadata = self._get_region_metadata(region_id)
                metadata['distance_km'] = distance_km
                self.assignment_stats['nearest_centroid'] += 1
                return region_id, 'nearest_centroid', metadata
        
        # Case 4: Outside all regions and too far from any centroid
        self.assignment_stats['outside_region'] += 1
        return -1, 'outside_region', {'distance_km': None}
    
    def assign_batch(
        self,
        lons: np.ndarray,
        lats: np.ndarray,
        cluster_probs: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """
        Assign multiple points to regions.
        
        Args:
            lons: Array of longitudes
            lats: Array of latitudes
            cluster_probs: Array of cluster probabilities (optional)
            
        Returns:
            DataFrame with assignments
        """
        logger.info(f"Assigning {len(lons)} points to regions...")
        
        self.assignment_stats = {
            'total': len(lons),
            'contained': 0,
            'nearest_centroid': 0,
            'outside_region': 0,
            'ambiguous': 0
        }
        
        results = []
        
        for i, (lon, lat) in enumerate(zip(lons, lats)):
            if i % 10000 == 0 and i > 0:
                logger.info(f"  Processed {i}/{len(lons)} points...")
            
            probs = cluster_probs[i] if cluster_probs is not None else None
            
            region_id, method, metadata = self.assign_point(lon, lat, probs)
            
            results.append({
                'longitude': lon,
                'latitude': lat,
                'region_id': region_id,
                'assignment_method': method,
                **metadata
            })
        
        results_df = pd.DataFrame(results)
        
        # Log statistics
        logger.info("Assignment statistics:")
        for key, value in self.assignment_stats.items():
            if key != 'total':
                pct = value / self.assignment_stats['total'] * 100
                logger.info(f"  {key}: {value} ({pct:.1f}%)")
        
        return results_df
    
    def _resolve_ambiguity_by_prob(
        self,
        containing_regions: List[Tuple[int, int]],
        cluster_probs: np.ndarray
    ) -> int:
        """Resolve ambiguity using cluster probabilities."""
        # Find region with highest probability
        best_region_id = None
        best_prob = -1
        
        for region_id, _ in containing_regions:
            if region_id < len(cluster_probs):
                prob = cluster_probs[region_id]
                if prob > best_prob:
                    best_prob = prob
                    best_region_id = region_id
        
        if best_region_id is not None:
            return best_region_id
        
        # Fallback to distance
        return self._resolve_ambiguity_by_distance(
            containing_regions,
            0, 0  # Will use centroids
        )
    
    def _resolve_ambiguity_by_distance(
        self,
        containing_regions: List[Tuple[int, int]],
        lon: float,
        lat: float
    ) -> int:
        """Resolve ambiguity by finding nearest centroid."""
        point = Point(lon, lat)
        
        min_distance = float('inf')
        nearest_region_id = containing_regions[0][0]
        
        for region_id, _ in containing_regions:
            metadata = self.metadata_df[self.metadata_df['region_id'] == region_id].iloc[0]
            centroid = Point(metadata['centroid_lon'], metadata['centroid_lat'])
            distance = point.distance(centroid)
            
            if distance < min_distance:
                min_distance = distance
                nearest_region_id = region_id
        
        return nearest_region_id
    
    def _find_nearest_centroid(
        self,
        lon: float,
        lat: float
    ) -> Tuple[int, float]:
        """
        Find nearest region centroid.
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            Tuple of (region_id, distance_km)
        """
        point = Point(lon, lat)
        
        min_distance = float('inf')
        nearest_region_id = -1
        
        for _, row in self.metadata_df.iterrows():
            centroid = Point(row['centroid_lon'], row['centroid_lat'])
            distance_deg = point.distance(centroid)
            distance_km = distance_deg * 111.0  # Approximate
            
            if distance_km < min_distance:
                min_distance = distance_km
                nearest_region_id = row['region_id']
        
        return nearest_region_id, min_distance
    
    def _get_region_metadata(self, region_id: int) -> Dict:
        """Get metadata for a region."""
        if region_id < 0:
            return {}
        
        metadata_row = self.metadata_df[self.metadata_df['region_id'] == region_id]
        
        if len(metadata_row) == 0:
            return {}
        
        metadata = metadata_row.iloc[0].to_dict()
        
        # Return subset of useful fields
        return {
            'centroid_lat': metadata.get('centroid_lat'),
            'centroid_lon': metadata.get('centroid_lon'),
            'max_dist_km': metadata.get('max_dist_km'),
            'n_profiles': metadata.get('n_profiles')
        }
    
    def get_assignment_stats(self) -> Dict:
        """Get assignment statistics."""
        return self.assignment_stats.copy()
    
    def visualize_assignment(
        self,
        lon: float,
        lat: float,
        save_path: Optional[str] = None
    ):
        """
        Visualize point assignment (for debugging).
        
        Args:
            lon: Longitude
            lat: Latitude
            save_path: Path to save figure (optional)
        """
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot polygons
        self.polygons_gdf.plot(ax=ax, alpha=0.3, edgecolor='black')
        
        # Plot centroids
        for _, row in self.metadata_df.iterrows():
            ax.plot(
                row['centroid_lon'],
                row['centroid_lat'],
                'ro',
                markersize=8
            )
            ax.text(
                row['centroid_lon'],
                row['centroid_lat'],
                f"R{row['region_id']}",
                fontsize=10
            )
        
        # Plot query point
        ax.plot(lon, lat, 'b*', markersize=20, label='Query Point')
        
        # Assign and show result
        region_id, method, metadata = self.assign_point(lon, lat)
        
        if region_id >= 0:
            # Highlight assigned region
            assigned_poly = self.polygons_gdf[
                self.polygons_gdf['region_id'] == region_id
            ]
            assigned_poly.plot(ax=ax, color='green', alpha=0.5)
            
            title = f"Assigned to Region {region_id} ({method})"
        else:
            title = "Outside all regions"
        
        ax.set_title(title)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Visualization saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
