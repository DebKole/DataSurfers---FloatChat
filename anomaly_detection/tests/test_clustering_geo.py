"""
Test script for clustering and geospatial operations.
"""

import sys
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import DataLoader
from features.oceanographic import OceanographicFeatures
from clustering.clusterer import RegionalClusterer
from clustering.polygons import PolygonGenerator
from clustering.validator import ClusterValidator
from geo.pip_assign import PointInPolygonAssigner
from geo.distance_weights import DistanceWeighting

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def prepare_features(profiles, measurements, config):
    """Prepare features for clustering."""
    logger.info("Computing features for clustering...")
    
    features_list = []
    
    for profile_id in profiles['global_profile_id'].unique()[:1000]:  # Test with 1000 profiles
        profile_meta = profiles[profiles['global_profile_id'] == profile_id].iloc[0]
        profile_data = measurements[measurements['global_profile_id'] == profile_id].sort_values('pressure')
        
        if len(profile_data) < 3:
            continue
        
        temp = profile_data['temperature'].values
        sal = profile_data['salinity'].values
        pres = profile_data['pressure'].values
        lat = profile_meta['latitude']
        lon = profile_meta['longitude']
        
        # Extract surface values
        temp_surf, sal_surf = OceanographicFeatures.extract_surface_values(temp, sal, pres, 0)
        temp_200, sal_200 = OceanographicFeatures.extract_surface_values(temp, sal, pres, 200)
        
        # Compute features
        try:
            density_surf = OceanographicFeatures.compute_density(
                np.array([temp_surf]), np.array([sal_surf]), np.array([0]), lat, lon
            )[0]
            
            mld = OceanographicFeatures.compute_mld(temp, sal, pres, lat, lon)
            therm_depth = OceanographicFeatures.compute_thermocline_depth(temp, pres)
            
            # Scale lat/lon
            lat_scaled = lat / 40.0
            lon_scaled = lon / 40.0
            
            features_list.append({
                'global_profile_id': profile_id,
                'latitude': lat,
                'longitude': lon,
                'temp_surface': temp_surf,
                'temp_200m': temp_200,
                'salinity_surface': sal_surf,
                'salinity_200m': sal_200,
                'density_surface': density_surf,
                'mld': mld,
                'thermocline_depth': therm_depth,
                'latitude_scaled': lat_scaled,
                'longitude_scaled': lon_scaled
            })
        except Exception as e:
            logger.warning(f"Error computing features for profile {profile_id}: {e}")
            continue
    
    features_df = pd.DataFrame(features_list)
    logger.info(f"Computed features for {len(features_df)} profiles")
    
    return features_df


def test_clustering(features_df, config):
    """Test clustering."""
    logger.info("=" * 80)
    logger.info("Testing Clustering")
    logger.info("=" * 80)
    
    # Initialize clusterer
    clusterer = RegionalClusterer(config)
    
    # Fit clustering
    results = clusterer.fit(features_df, use_pca=True, use_hdbscan=True)
    
    logger.info(f"Found {results['n_clusters']} clusters")
    logger.info("\nCluster statistics:")
    print(results['cluster_stats'])
    
    # Validate clustering
    validator = ClusterValidator()
    
    # Compute metrics
    X_scaled = clusterer.scaler.transform(
        features_df[results['feature_names']].dropna().values
    )
    if clusterer.pca is not None:
        X_transformed = clusterer.pca.transform(X_scaled)
    else:
        X_transformed = X_scaled
    
    metrics = validator.compute_metrics(X_transformed, results['cluster_labels'])
    logger.info("\nClustering metrics:")
    for metric, value in metrics.items():
        logger.info(f"  {metric}: {value:.3f}")
    
    # Save clusterer
    clusterer.save("artifacts/models/clusterer.pkl")
    
    return clusterer, results


def test_polygon_generation(features_df, cluster_labels, cluster_probs, config):
    """Test polygon generation."""
    logger.info("=" * 80)
    logger.info("Testing Polygon Generation")
    logger.info("=" * 80)
    
    # Initialize polygon generator
    poly_gen = PolygonGenerator(config)
    
    # Generate polygons
    polygons_gdf, metadata_df = poly_gen.generate_polygons(
        features_df, cluster_labels, cluster_probs
    )
    
    logger.info(f"Generated {len(polygons_gdf)} polygons")
    logger.info("\nPolygon metadata:")
    print(metadata_df[['region_id', 'n_profiles', 'area_km2', 'max_dist_km']])
    
    # Save polygons
    poly_gen.save("artifacts/polygons/")
    
    return poly_gen, polygons_gdf, metadata_df


def test_pip_assignment(features_df, polygons_gdf, metadata_df, config):
    """Test point-in-polygon assignment."""
    logger.info("=" * 80)
    logger.info("Testing Point-in-Polygon Assignment")
    logger.info("=" * 80)
    
    # Initialize PIP assigner
    pip_assigner = PointInPolygonAssigner(polygons_gdf, metadata_df, config)
    
    # Test single point assignment
    test_lon, test_lat = features_df.iloc[0]['longitude'], features_df.iloc[0]['latitude']
    region_id, method, metadata = pip_assigner.assign_point(test_lon, test_lat)
    
    logger.info(f"Test point ({test_lon:.2f}, {test_lat:.2f}):")
    logger.info(f"  Assigned to region: {region_id}")
    logger.info(f"  Method: {method}")
    logger.info(f"  Metadata: {metadata}")
    
    # Test batch assignment
    lons = features_df['longitude'].values[:100]
    lats = features_df['latitude'].values[:100]
    
    assignments_df = pip_assigner.assign_batch(lons, lats)
    
    logger.info("\nBatch assignment results:")
    print(assignments_df['assignment_method'].value_counts())
    
    logger.info("\nAssignment statistics:")
    stats = pip_assigner.get_assignment_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return pip_assigner, assignments_df


def test_distance_weighting(features_df, metadata_df, config):
    """Test distance weighting."""
    logger.info("=" * 80)
    logger.info("Testing Distance Weighting")
    logger.info("=" * 80)
    
    # Initialize distance weighting
    dist_weight = DistanceWeighting(config)
    
    # Test for first region
    region_id = metadata_df.iloc[0]['region_id']
    region_metadata = metadata_df.iloc[0]
    
    # Get samples in this region (simulate)
    region_data = features_df.sample(min(100, len(features_df)))
    
    # Compute weights
    weights = dist_weight.compute_weights_for_region(
        region_data, region_metadata
    )
    
    logger.info(f"\nWeights for region {region_id}:")
    logger.info(f"  Min: {weights.min():.3f}")
    logger.info(f"  Max: {weights.max():.3f}")
    logger.info(f"  Mean: {weights.mean():.3f}")
    logger.info(f"  Std: {weights.std():.3f}")
    
    return dist_weight, weights


def main():
    """Run all tests."""
    logger.info("Starting clustering and geospatial operations tests...")
    
    # Load configuration
    config = load_config()
    
    # Load data (small sample for testing)
    logger.info("Loading data...")
    loader = DataLoader(config)
    profiles = loader.load_profiles_csv('2019-01-01', '2019-01-07')
    measurements = loader.load_measurements_csv(
        profile_ids=profiles['global_profile_id'].unique()
    )
    
    # Prepare features
    features_df = prepare_features(profiles, measurements, config)
    
    # Test clustering
    clusterer, cluster_results = test_clustering(features_df, config)
    
    # Test polygon generation
    poly_gen, polygons_gdf, metadata_df = test_polygon_generation(
        features_df,
        cluster_results['cluster_labels'],
        cluster_results['cluster_probs'],
        config
    )
    
    # Test PIP assignment
    pip_assigner, assignments_df = test_pip_assignment(
        features_df, polygons_gdf, metadata_df, config
    )
    
    # Test distance weighting
    dist_weight, weights = test_distance_weighting(
        features_df, metadata_df, config
    )
    
    logger.info("=" * 80)
    logger.info("All tests completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
