"""
Polygon generation from clustered points using alpha shapes.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict, List, Tuple, Optional
import alphashape
import logging

logger = logging.getLogger(__name__)


class PolygonGenerator:
    """Generate concave hull polygons from clustered points."""
    
    def __init__(self, config: Dict):
        """
        Initialize polygon generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("clustering", {}).get("polygons", {})
        self.polygons = None
        self.metadata = None
        
    def generate_polygons(
        self,
        features_df: pd.DataFrame,
        cluster_labels: np.ndarray,
        cluster_probs: Optional[np.ndarray] = None
    ) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
        """
        Generate polygons for each cluster.
        
        Args:
            features_df: DataFrame with lat/lon
            cluster_labels: Cluster assignments
            cluster_probs: Cluster probabilities (optional)
            
        Returns:
            Tuple of (GeoDataFrame with polygons, metadata DataFrame)
        """
        alpha = self.config.get("alpha", 0.0)
        buffer_km = self.config.get("buffer_km", 50)
        simplify_tolerance = self.config.get("simplify_tolerance", 0.01)
        min_area_km2 = self.config.get("min_area_km2", 10000)
        
        logger.info("Generating polygons for clusters...")
        
        polygons_list = []
        metadata_list = []
        
        unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
        
        for cluster_id in unique_clusters:
            logger.info(f"  Processing cluster {cluster_id}...")
            
            # Get points in this cluster
            cluster_mask = cluster_labels == cluster_id
            cluster_data = features_df[cluster_mask].copy()
            
            if len(cluster_data) < 3:
                logger.warning(f"    Cluster {cluster_id} has < 3 points, skipping")
                continue
            
            # Extract coordinates
            points = cluster_data[['longitude', 'latitude']].values
            
            # Generate alpha shape
            try:
                polygon = self._generate_alpha_shape(
                    points, alpha, buffer_km, simplify_tolerance
                )
                
                if polygon is None or polygon.is_empty:
                    logger.warning(f"    Failed to generate polygon for cluster {cluster_id}")
                    continue
                
                # Check minimum area
                area_km2 = self._compute_area_km2(polygon)
                
                if area_km2 < min_area_km2:
                    logger.warning(f"    Cluster {cluster_id} area ({area_km2:.0f} km²) "
                                 f"below minimum ({min_area_km2} km²)")
                    continue
                
                # Compute metadata
                metadata = self._compute_polygon_metadata(
                    cluster_id, polygon, cluster_data, cluster_probs
                )
                
                polygons_list.append({
                    'region_id': cluster_id,
                    'geometry': polygon
                })
                
                metadata_list.append(metadata)
                
                logger.info(f"    Created polygon: {len(cluster_data)} points, "
                          f"{area_km2:.0f} km²")
                
            except Exception as e:
                logger.error(f"    Error generating polygon for cluster {cluster_id}: {e}")
                continue
        
        # Create GeoDataFrame
        if not polygons_list:
            raise ValueError("No valid polygons generated")
        
        self.polygons = gpd.GeoDataFrame(
            polygons_list,
            crs="EPSG:4326"
        )
        
        self.metadata = pd.DataFrame(metadata_list)
        
        logger.info(f"Generated {len(self.polygons)} polygons")
        
        return self.polygons, self.metadata
    
    def _generate_alpha_shape(
        self,
        points: np.ndarray,
        alpha: float,
        buffer_km: float,
        simplify_tolerance: float
    ) -> Optional[Polygon]:
        """
        Generate alpha shape (concave hull) from points.
        
        Args:
            points: Array of (lon, lat) coordinates
            alpha: Alpha parameter (0 = auto)
            buffer_km: Buffer distance in km
            simplify_tolerance: Simplification tolerance
            
        Returns:
            Polygon or None
        """
        try:
            # Generate alpha shape
            if alpha == 0.0:
                # Auto-select alpha
                alpha_shape = alphashape.alphashape(points)
            else:
                alpha_shape = alphashape.alphashape(points, alpha)
            
            # Handle MultiPolygon (take largest)
            if isinstance(alpha_shape, MultiPolygon):
                alpha_shape = max(alpha_shape.geoms, key=lambda p: p.area)
            
            if not isinstance(alpha_shape, Polygon):
                return None
            
            # Buffer (convert km to degrees, approximate)
            buffer_deg = buffer_km / 111.0  # 1 degree ≈ 111 km
            polygon = alpha_shape.buffer(buffer_deg)
            
            # Simplify
            if simplify_tolerance > 0:
                polygon = polygon.simplify(simplify_tolerance, preserve_topology=True)
            
            # Clean up
            if not polygon.is_valid:
                polygon = polygon.buffer(0)
            
            return polygon
            
        except Exception as e:
            logger.error(f"Error in alpha shape generation: {e}")
            return None
    
    def _compute_area_km2(self, polygon: Polygon) -> float:
        """
        Compute polygon area in km².
        
        Args:
            polygon: Shapely polygon
            
        Returns:
            Area in km²
        """
        # Create temporary GeoDataFrame for area calculation
        gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
        
        # Project to equal-area projection (World Mollweide)
        gdf_proj = gdf.to_crs("ESRI:54009")
        
        # Compute area in m² and convert to km²
        area_m2 = gdf_proj.geometry.area.iloc[0]
        area_km2 = area_m2 / 1e6
        
        return area_km2
    
    def _compute_polygon_metadata(
        self,
        cluster_id: int,
        polygon: Polygon,
        cluster_data: pd.DataFrame,
        cluster_probs: Optional[np.ndarray]
    ) -> Dict:
        """
        Compute metadata for a polygon.
        
        Args:
            cluster_id: Cluster ID
            polygon: Polygon geometry
            cluster_data: Data points in cluster
            cluster_probs: Cluster probabilities
            
        Returns:
            Dictionary with metadata
        """
        # Centroid
        centroid = polygon.centroid
        centroid_lat = centroid.y
        centroid_lon = centroid.x
        
        # Bounding box
        bounds = polygon.bounds  # (minx, miny, maxx, maxy)
        
        # Area
        area_km2 = self._compute_area_km2(polygon)
        
        # Number of profiles
        n_profiles = len(cluster_data)
        
        # Maximum distance from centroid
        distances = []
        for _, row in cluster_data.iterrows():
            point = Point(row['longitude'], row['latitude'])
            dist_deg = point.distance(centroid)
            dist_km = dist_deg * 111.0  # Approximate
            distances.append(dist_km)
        
        max_dist_km = max(distances) if distances else 0.0
        mean_dist_km = np.mean(distances) if distances else 0.0
        
        # Average cluster probability (if available)
        avg_prob = None
        if cluster_probs is not None:
            cluster_mask = cluster_data.index
            avg_prob = cluster_probs[cluster_mask, cluster_id].mean()
        
        metadata = {
            'region_id': cluster_id,
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
            'area_km2': area_km2,
            'n_profiles': n_profiles,
            'max_dist_km': max_dist_km,
            'mean_dist_km': mean_dist_km,
            'bbox_minx': bounds[0],
            'bbox_miny': bounds[1],
            'bbox_maxx': bounds[2],
            'bbox_maxy': bounds[3],
            'avg_cluster_prob': avg_prob
        }
        
        # Add oceanographic statistics if available
        for col in ['temp_surface', 'salinity_surface', 'mld', 'thermocline_depth']:
            if col in cluster_data.columns:
                metadata[f'{col}_mean'] = cluster_data[col].mean()
                metadata[f'{col}_std'] = cluster_data[col].std()
                metadata[f'{col}_min'] = cluster_data[col].min()
                metadata[f'{col}_max'] = cluster_data[col].max()
        
        return metadata
    
    def clip_to_ocean(self, ocean_mask_path: Optional[str] = None):
        """
        Clip polygons to ocean boundaries.
        
        Args:
            ocean_mask_path: Path to ocean mask shapefile
        """
        if self.polygons is None:
            raise ValueError("No polygons generated yet")
        
        if ocean_mask_path is None:
            logger.warning("No ocean mask provided, skipping clipping")
            return
        
        try:
            logger.info("Clipping polygons to ocean boundaries...")
            
            # Load ocean mask
            ocean_mask = gpd.read_file(ocean_mask_path)
            
            # Clip each polygon
            clipped_polygons = []
            for idx, row in self.polygons.iterrows():
                clipped = gpd.overlay(
                    gpd.GeoDataFrame([row], crs=self.polygons.crs),
                    ocean_mask,
                    how='intersection'
                )
                
                if len(clipped) > 0:
                    clipped_polygons.append(clipped.iloc[0])
            
            self.polygons = gpd.GeoDataFrame(clipped_polygons, crs=self.polygons.crs)
            
            logger.info(f"Clipped to {len(self.polygons)} ocean polygons")
            
        except Exception as e:
            logger.error(f"Error clipping to ocean: {e}")
    
    def merge_small_regions(
        self,
        min_profiles: int = 1000,
        features_df: Optional[pd.DataFrame] = None
    ):
        """
        Merge small regions with neighbors.
        
        Args:
            min_profiles: Minimum number of profiles per region
            features_df: DataFrame with features for recomputing metadata
        """
        if self.polygons is None or self.metadata is None:
            raise ValueError("No polygons generated yet")
        
        logger.info(f"Merging regions with < {min_profiles} profiles...")
        
        small_regions = self.metadata[self.metadata['n_profiles'] < min_profiles]
        
        if len(small_regions) == 0:
            logger.info("No small regions to merge")
            return
        
        logger.info(f"Found {len(small_regions)} small regions")
        
        # For each small region, find nearest neighbor and merge
        for _, small_region in small_regions.iterrows():
            region_id = small_region['region_id']
            
            # Find nearest neighbor
            small_poly = self.polygons[self.polygons['region_id'] == region_id].iloc[0]
            small_centroid = small_poly.geometry.centroid
            
            # Compute distances to other regions
            distances = []
            for _, other_region in self.metadata.iterrows():
                if other_region['region_id'] == region_id:
                    continue
                
                other_centroid = Point(
                    other_region['centroid_lon'],
                    other_region['centroid_lat']
                )
                
                dist = small_centroid.distance(other_centroid)
                distances.append((other_region['region_id'], dist))
            
            if not distances:
                continue
            
            # Merge with nearest
            nearest_id, _ = min(distances, key=lambda x: x[1])
            
            logger.info(f"  Merging region {region_id} into region {nearest_id}")
            
            # Merge polygons
            small_geom = self.polygons[self.polygons['region_id'] == region_id].iloc[0].geometry
            nearest_geom = self.polygons[self.polygons['region_id'] == nearest_id].iloc[0].geometry
            
            merged_geom = unary_union([small_geom, nearest_geom])
            
            # Update polygon
            self.polygons.loc[self.polygons['region_id'] == nearest_id, 'geometry'] = merged_geom
            
            # Remove small region
            self.polygons = self.polygons[self.polygons['region_id'] != region_id]
            self.metadata = self.metadata[self.metadata['region_id'] != region_id]
        
        logger.info(f"After merging: {len(self.polygons)} regions")
    
    def save(self, output_dir: str):
        """
        Save polygons and metadata.
        
        Args:
            output_dir: Output directory
        """
        from pathlib import Path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.polygons is not None:
            # Save as GeoJSON
            geojson_path = output_dir / "regions.geojson"
            self.polygons.to_file(geojson_path, driver="GeoJSON")
            logger.info(f"Polygons saved to {geojson_path}")
            
            # Save as Shapefile
            shp_path = output_dir / "regions.shp"
            self.polygons.to_file(shp_path)
            logger.info(f"Polygons saved to {shp_path}")
        
        if self.metadata is not None:
            # Save metadata as CSV
            csv_path = output_dir / "regions_metadata.csv"
            self.metadata.to_csv(csv_path, index=False)
            logger.info(f"Metadata saved to {csv_path}")
            
            # Save as JSON
            json_path = output_dir / "regions_metadata.json"
            self.metadata.to_json(json_path, orient='records', indent=2)
            logger.info(f"Metadata saved to {json_path}")
    
    @classmethod
    def load(cls, polygons_path: str, metadata_path: str, config: Dict) -> 'PolygonGenerator':
        """
        Load polygons and metadata from files.
        
        Args:
            polygons_path: Path to GeoJSON or Shapefile
            metadata_path: Path to metadata CSV
            config: Configuration dictionary
            
        Returns:
            PolygonGenerator instance
        """
        generator = cls(config)
        
        generator.polygons = gpd.read_file(polygons_path)
        generator.metadata = pd.read_csv(metadata_path)
        
        logger.info(f"Loaded {len(generator.polygons)} polygons from {polygons_path}")
        
        return generator
