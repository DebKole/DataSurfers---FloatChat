"""
Complete pipeline: Train models and detect anomalies.
"""

import sys
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import DataLoader
from features.oceanographic import OceanographicFeatures
from clustering.clusterer import RegionalClusterer
from clustering.polygons import PolygonGenerator
from geo.pip_assign import PointInPolygonAssigner
from geo.distance_weights import DistanceWeighting
from models.trainer import RegionalTrainer
from models.predictor import RegionalPredictor
from anomaly.detectors import AnomalyDetectorEnsemble
from anomaly.fusion import ScoreFusion
from validation.metrics import ValidationMetrics

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
    """Prepare features for clustering and modeling."""
    logger.info("Computing features...")
    
    features_list = []
    
    for profile_id in profiles['global_profile_id'].unique():
        profile_meta = profiles[profiles['global_profile_id'] == profile_id].iloc[0]
        profile_data = measurements[measurements['global_profile_id'] == profile_id].sort_values('pressure')
        
        if len(profile_data) < 3:
            continue
        
        temp = profile_data['temperature'].values
        sal = profile_data['salinity'].values
        pres = profile_data['pressure'].values
        lat = profile_meta['latitude']
        lon = profile_meta['longitude']
        
        try:
            temp_surf, sal_surf = OceanographicFeatures.extract_surface_values(temp, sal, pres, 0)
            temp_200, sal_200 = OceanographicFeatures.extract_surface_values(temp, sal, pres, 200)
            
            density_surf = OceanographicFeatures.compute_density(
                np.array([temp_surf]), np.array([sal_surf]), np.array([0]), lat, lon
            )[0]
            
            mld = OceanographicFeatures.compute_mld(temp, sal, pres, lat, lon)
            therm_depth = OceanographicFeatures.compute_thermocline_depth(temp, pres)
            
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
                'latitude_scaled': lat / 40.0,
                'longitude_scaled': lon / 40.0
            })
        except Exception as e:
            continue
    
    features_df = pd.DataFrame(features_list)
    logger.info(f"Computed features for {len(features_df)} profiles")
    
    return features_df


def main():
    """Run complete pipeline."""
    logger.info("="*80)
    logger.info("ARGO ANOMALY DETECTION - COMPLETE PIPELINE")
    logger.info("="*80)
    
    config = load_config()
    
    # 1. Load data
    logger.info("\n[1/8] Loading data...")
    loader = DataLoader(config)
    profiles = loader.load_profiles_csv(
        start_date=config['data'].get('start_date', '2022-01-01'),
        end_date=config['data'].get('end_date', '2024-12-31')
    )
    measurements = loader.load_measurements_csv(
        profile_ids=profiles['global_profile_id'].unique()
    )
    
    # 2. Compute features
    logger.info("\n[2/7] Computing features...")
    measurements_clean = measurements
    
    # 3. Extract features
    logger.info("\n[3/8] Computing features...")
    features_df = prepare_features(profiles, measurements_clean, config)
    
    # 4. Cluster and generate polygons
    logger.info("\n[4/8] Clustering profiles...")
    clusterer = RegionalClusterer(config)
    cluster_results = clusterer.fit(features_df)
    
    poly_gen = PolygonGenerator(config)
    polygons_gdf, metadata_df = poly_gen.generate_polygons(
        features_df,
        cluster_results['cluster_labels'],
        cluster_results['cluster_probs']
    )
    
    # Save artifacts
    clusterer.save("artifacts/models/clusterer.pkl")
    poly_gen.save("artifacts/polygons/")
    
    # 5. Assign regions and compute weights
    logger.info("\n[5/8] Assigning regions and computing weights...")
    pip_assigner = PointInPolygonAssigner(polygons_gdf, metadata_df, config)
    
    assignments = pip_assigner.assign_batch(
        features_df['longitude'].values,
        features_df['latitude'].values
    )
    
    features_df['region_id'] = assignments['region_id'].values
    
    # Compute weights per region
    dist_weight = DistanceWeighting(config)
    weights_dict = {}
    
    for region_id in metadata_df['region_id'].unique():
        region_data = features_df[features_df['region_id'] == region_id]
        if len(region_data) == 0:
            continue
        
        region_metadata = metadata_df[metadata_df['region_id'] == region_id].iloc[0]
        weights = dist_weight.compute_weights_for_region(region_data, region_metadata)
        weights_dict[region_id] = weights
    
    # 6. Train regional models
    logger.info("\n[6/8] Training regional models...")
    trainer = RegionalTrainer(config)
    
    training_results = trainer.train_all_regions(
        measurements_clean,
        features_df,
        features_df[['global_profile_id', 'region_id']],
        weights_dict,
        metadata_df
    )
    
    trainer.save("artifacts/models/regional_models/")
    
    # 7. Detect anomalies
    logger.info("\n[7/8] Detecting anomalies...")
    predictor = RegionalPredictor(trainer)
    detector = AnomalyDetectorEnsemble(config)
    fusion = ScoreFusion(config)
    
    # Collect predictions and residuals for fitting detectors
    all_residuals = []
    all_features = []
    
    for region_id in training_results['models'].keys():
        region_profiles = features_df[features_df['region_id'] == region_id]['global_profile_id'].values
        region_measurements = measurements_clean[
            measurements_clean['global_profile_id'].isin(region_profiles)
        ].head(1000)  # Sample for speed
        
        if len(region_measurements) == 0:
            continue
        
        # Prepare features
        X, y, _, feature_names = trainer.prepare_training_data(
            region_measurements, features_df, region_id
        )
        
        # Predict
        temp_pred, sal_pred = predictor.predict(X, region_id)
        
        # Collect residuals
        temp_residuals = y[:, 0] - temp_pred
        sal_residuals = y[:, 1] - sal_pred
        all_residuals.extend(temp_residuals)
        all_residuals.extend(sal_residuals)
        
        # Collect profile features
        for profile_id in region_profiles[:100]:
            profile_features = features_df[features_df['global_profile_id'] == profile_id]
            if len(profile_features) > 0:
                feat_vec = profile_features[[
                    'temp_surface', 'salinity_surface', 'mld', 'thermocline_depth'
                ]].values[0]
                all_features.append(feat_vec)
    
    # Fit detectors
    all_residuals = np.array(all_residuals)
    all_features = np.array(all_features)
    
    detector.fit(all_features, all_residuals)
    
    # Detect anomalies on test profiles
    anomaly_results = []
    
    for region_id in list(training_results['models'].keys())[:3]:  # Test on first 3 regions
        region_profiles = features_df[features_df['region_id'] == region_id]['global_profile_id'].values[:10]
        
        for profile_id in region_profiles:
            profile_data = measurements_clean[measurements_clean['global_profile_id'] == profile_id]
            profile_features = features_df[features_df['global_profile_id'] == profile_id]
            
            if len(profile_data) == 0 or len(profile_features) == 0:
                continue
            
            # Prepare and predict
            X, y, _, _ = trainer.prepare_training_data(profile_data, features_df, region_id)
            temp_pred, sal_pred = predictor.predict(X, region_id)
            
            predictions_df = pd.DataFrame({
                'temperature_pred': temp_pred,
                'salinity_pred': sal_pred
            })
            
            # Detect anomalies
            feat_vec = profile_features[[
                'temp_surface', 'salinity_surface', 'mld', 'thermocline_depth'
            ]].values[0]
            
            scores = detector.detect_profile(
                profile_data, predictions_df, feat_vec, weight=1.0
            )
            
            fused_score, alert_level = fusion.fuse_profile_scores(scores)
            
            anomaly_results.append({
                'profile_id': profile_id,
                'region_id': region_id,
                'fused_score': fused_score,
                'alert_level': alert_level,
                **scores
            })
    
    anomaly_df = pd.DataFrame(anomaly_results)
    anomaly_df.to_csv("artifacts/results/anomaly_detection_results.csv", index=False)
    
    logger.info(f"\nDetected anomalies:")
    logger.info(f"  Total profiles analyzed: {len(anomaly_df)}")
    logger.info(f"  Alert distribution:")
    print(anomaly_df['alert_level'].value_counts())
    
    # 8. Validation
    logger.info("\n[8/8] Validation...")
    
    # Compute overall metrics
    all_temp_true = []
    all_temp_pred = []
    all_sal_true = []
    all_sal_pred = []
    
    for region_id in list(training_results['models'].keys())[:3]:
        region_profiles = features_df[features_df['region_id'] == region_id]['global_profile_id'].values[:50]
        region_measurements = measurements_clean[
            measurements_clean['global_profile_id'].isin(region_profiles)
        ]
        
        if len(region_measurements) == 0:
            continue
        
        X, y, _, _ = trainer.prepare_training_data(region_measurements, features_df, region_id)
        temp_pred, sal_pred = predictor.predict(X, region_id)
        
        all_temp_true.extend(y[:, 0])
        all_temp_pred.extend(temp_pred)
        all_sal_true.extend(y[:, 1])
        all_sal_pred.extend(sal_pred)
    
    temp_metrics = ValidationMetrics.compute_regression_metrics(
        np.array(all_temp_true), np.array(all_temp_pred)
    )
    sal_metrics = ValidationMetrics.compute_regression_metrics(
        np.array(all_sal_true), np.array(all_sal_pred)
    )
    
    logger.info("\nValidation Metrics:")
    logger.info(f"Temperature - RMSE: {temp_metrics['rmse']:.4f}, MAE: {temp_metrics['mae']:.4f}, R²: {temp_metrics['r2']:.4f}")
    logger.info(f"Salinity - RMSE: {sal_metrics['rmse']:.4f}, MAE: {sal_metrics['mae']:.4f}, R²: {sal_metrics['r2']:.4f}")
    
    logger.info("\n" + "="*80)
    logger.info("PIPELINE COMPLETE!")
    logger.info("="*80)
    logger.info(f"Models saved to: artifacts/models/")
    logger.info(f"Polygons saved to: artifacts/polygons/")
    logger.info(f"Results saved to: artifacts/results/")


if __name__ == "__main__":
    main()
