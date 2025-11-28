#!/usr/bin/env python3
"""
Quick Test Script for Argo Anomaly Detection System

This script performs a quick end-to-end test of the system:
1. Load sample data
2. Apply QC
3. Extract features
4. Run clustering (if needed)
5. Train models (if needed)
6. Detect anomalies
7. Display results

Usage:
    python pipeline/quick_test.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import system components
from data.loader import DataLoader
from features.engineer import FeatureEngineer
from clustering.clusterer import RegionalClusterer
from geo.pip_assign import PointInPolygonAssigner
from models.trainer import RegionalTrainer
from models.predictor import RegionalPredictor
from anomaly.detectors import AnomalyDetectorEnsemble
from anomaly.fusion import ScoreFusion


def main():
    """Run quick test of the system."""
    
    print("=" * 80)
    print("ARGO ANOMALY DETECTION SYSTEM - QUICK TEST")
    print("=" * 80)
    print()
    
    # Load configuration
    print("📋 Loading configuration...")
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    print("✅ Configuration loaded")
    print()
    
    # Step 1: Load data
    print("📊 Step 1: Loading sample data...")
    loader = DataLoader(config)
    
    try:
        profiles = loader.load_profiles_csv(
            start_date='2019-01-01',
            end_date='2019-01-07'
        )
        print(f"✅ Loaded {len(profiles)} profiles")
        
        measurements = loader.load_measurements_csv(
            profile_ids=profiles['global_profile_id'].unique()
        )
        print(f"✅ Loaded {len(measurements)} measurements")
        print()
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("   Make sure your data files are in the correct location.")
        print(f"   Expected path: {config['paths']['data']}")
        return
    
    # Step 2: Extract features
    print("🔧 Step 2: Extracting features...")
    measurements_clean = measurements
    engineer = FeatureEngineer(config)
    
    # Use subset for quick test
    sample_size = min(100, len(profiles))
    sample_profiles = profiles.head(sample_size)
    
    features_df = engineer.process_profiles_batch(
        sample_profiles,
        measurements_clean
    )
    
    print(f"✅ Extracted features for {len(features_df)} profiles")
    print(f"   Number of features: {len(engineer.feature_names)}")
    print()
    
    # Step 3: Clustering
    print("🗺️  Step 3: Regional clustering...")
    clusterer = RegionalClusterer(config)
    
    # Get feature matrix
    X, feature_names = engineer.get_feature_matrix(features_df)
    coords = features_df[['longitude', 'latitude']].values
    
    # Perform clustering
    cluster_labels = clusterer.fit_predict(X, coords)
    features_df['cluster_id'] = cluster_labels
    
    n_clusters = len(np.unique(cluster_labels[cluster_labels >= 0]))
    n_outliers = np.sum(cluster_labels == -1)
    
    print(f"✅ Clustering complete:")
    print(f"   Clusters: {n_clusters}")
    print(f"   Outliers: {n_outliers}")
    print()
    
    # Step 4: Train models (simplified)
    print("🤖 Step 4: Training regional models...")
    trainer = RegionalTrainer(config)
    
    # Train on subset
    train_size = int(len(features_df) * 0.7)
    train_df = features_df.head(train_size)
    
    try:
        models = trainer.train_all_regions(
            train_df,
            cluster_col='cluster_id'
        )
        
        print(f"✅ Trained {len(models)} regional models")
        print()
        
    except Exception as e:
        print(f"⚠️  Model training skipped: {e}")
        print("   Continuing with feature-based anomaly detection only...")
        models = {}
        print()
    
    # Step 5: Anomaly detection
    print("🚨 Step 5: Detecting anomalies...")
    detector = AnomalyDetectorEnsemble(config)
    
    # Fit detector on training data
    detector.fit(X[:train_size])
    
    # Detect on test data
    test_df = features_df.tail(len(features_df) - train_size)
    X_test, _ = engineer.get_feature_matrix(test_df)
    
    anomaly_scores = detector.detect(
        test_df,
        predictions=None,  # No predictions for this quick test
        cluster_ids=test_df['cluster_id'].values
    )
    
    # Analyze results
    threshold = 0.5
    n_anomalies = np.sum(anomaly_scores > threshold)
    anomaly_rate = n_anomalies / len(anomaly_scores)
    
    print(f"✅ Anomaly detection complete:")
    print(f"   Test profiles: {len(test_df)}")
    print(f"   Anomalies detected: {n_anomalies} ({anomaly_rate:.2%})")
    print(f"   Mean score: {np.mean(anomaly_scores):.3f}")
    print(f"   Max score: {np.max(anomaly_scores):.3f}")
    print()
    
    # Step 6: Display sample results
    print("📈 Step 6: Sample results...")
    print()
    
    # Show top 5 anomalies
    test_df['anomaly_score'] = anomaly_scores
    top_anomalies = test_df.nlargest(5, 'anomaly_score')
    
    print("Top 5 Anomalous Profiles:")
    print("-" * 80)
    for idx, row in top_anomalies.iterrows():
        print(f"Profile: {row.get('profile_id', 'N/A')}")
        print(f"  Location: ({row['latitude']:.2f}, {row['longitude']:.2f})")
        print(f"  Cluster: {row['cluster_id']}")
        print(f"  Anomaly Score: {row['anomaly_score']:.3f}")
        print(f"  Surface Temp: {row.get('surface_temp', 'N/A'):.2f}°C")
        print(f"  Surface Sal: {row.get('surface_sal', 'N/A'):.2f} PSU")
        print()
    
    # Summary
    print("=" * 80)
    print("✅ QUICK TEST COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✅ Data loading: {len(profiles)} profiles")
    print(f"  ✅ Feature extraction: {len(engineer.feature_names)} features")
    print(f"  ✅ Clustering: {n_clusters} regions")
    print(f"  ✅ Anomaly detection: {anomaly_rate:.2%} anomaly rate")
    print()
    print("Next steps:")
    print("  1. Run full pipeline: python pipeline/train_and_detect.py")
    print("  2. Start API server: python api/app.py")
    print("  3. Explore notebooks: jupyter notebook notebooks/")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        print("   Check the logs for details")
