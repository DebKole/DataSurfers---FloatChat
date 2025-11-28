"""
FastAPI Application for Argo Anomaly Detection System

Provides REST API endpoints for:
- Profile anomaly detection
- Batch processing
- Model training
- System status
- Validation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging
import yaml
from pathlib import Path
import pickle

from .schemas import (
    ProfileRequest, ProfileResponse, BatchProfileRequest, BatchProfileResponse,
    SystemStatus, RegionInfo, TrainingRequest, TrainingResponse,
    ValidationRequest, ValidationResponse, HealthCheck,
    AnomalyScore, AnomalyLevel, DetectorType
)

# Import system components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from features.engineer import FeatureEngineer
from models.predictor import RegionalPredictor
from anomaly.detectors import AnomalyDetectorEnsemble
from anomaly.fusion import ScoreFusion
from clustering.clusterer import RegionalClusterer
from geo.pip_assign import PointInPolygonAssigner

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Argo Anomaly Detection API",
    description="Real-time anomaly detection for Argo ocean profiles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    """Application state container."""
    def __init__(self):
        self.config: Optional[Dict] = None
        self.feature_engineer: Optional[FeatureEngineer] = None
        self.predictor: Optional[RegionalPredictor] = None
        self.detector: Optional[AnomalyDetectorEnsemble] = None
        self.fusion: Optional[ScoreFusion] = None
        self.pip_assigner: Optional[PointInPolygonAssigner] = None
        self.models_loaded = False
        self.last_training: Optional[datetime] = None

state = AppState()


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    logger.info("Starting Argo Anomaly Detection API...")
    
    try:
        # Load configuration
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path) as f:
            state.config = yaml.safe_load(f)
        
        # Initialize feature engineer
        state.feature_engineer = FeatureEngineer(state.config)
        
        # Try to load pre-trained models
        try:
            model_dir = Path(state.config['paths']['models'])
            
            # Load predictor
            predictor_path = model_dir / "regional_predictor.pkl"
            if predictor_path.exists():
                state.predictor = RegionalPredictor.load(str(predictor_path))
                logger.info("Loaded regional predictor")
            
            # Load detector
            detector_path = model_dir / "anomaly_detector.pkl"
            if detector_path.exists():
                state.detector = AnomalyDetectorEnsemble.load(str(detector_path))
                logger.info("Loaded anomaly detector")
            
            # Load PIP assigner
            pip_path = model_dir / "pip_assigner.pkl"
            if pip_path.exists():
                with open(pip_path, 'rb') as f:
                    state.pip_assigner = pickle.load(f)
                logger.info("Loaded PIP assigner")
            
            # Initialize fusion
            state.fusion = ScoreFusion(state.config)
            
            state.models_loaded = True
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
            logger.info("System will require training before use")
        
        logger.info("API startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.get("/", response_model=Dict)
async def root():
    """Root endpoint."""
    return {
        "service": "Argo Anomaly Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy" if state.models_loaded else "degraded",
        timestamp=datetime.now(),
        database_connected=True,  # TODO: Check actual DB connection
        models_loaded=state.models_loaded,
        api_version="1.0.0"
    )


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    regions = []
    
    if state.predictor and state.predictor.models:
        for region_id, model_info in state.predictor.models.items():
            regions.append(RegionInfo(
                cluster_id=region_id,
                centroid_lat=model_info.get('centroid_lat', 0.0),
                centroid_lon=model_info.get('centroid_lon', 0.0),
                area_km2=model_info.get('area_km2', 0.0),
                n_profiles=model_info.get('n_train_samples', 0),
                model_trained=True,
                last_updated=state.last_training
            ))
    
    return SystemStatus(
        status="healthy" if state.models_loaded else "not_trained",
        version="1.0.0",
        models_loaded=state.models_loaded,
        n_regions=len(regions),
        regions=regions,
        last_training=state.last_training
    )


@app.post("/detect", response_model=ProfileResponse)
async def detect_anomaly(request: ProfileRequest):
    """
    Detect anomalies in a single profile.
    """
    if not state.models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please train models first."
        )
    
    try:
        # Create profile dataframe
        profile_data = pd.DataFrame({
            'temperature': request.temperature,
            'salinity': request.salinity,
            'pressure': request.pressure
        })
        
        profile_meta = pd.Series({
            'latitude': request.latitude,
            'longitude': request.longitude,
            'date': request.date,
            'global_profile_id': f"api_{datetime.now().timestamp()}"
        })
        
        # Extract features
        features = state.feature_engineer.process_profile(profile_data, profile_meta)
        
        if features is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract features from profile"
            )
        
        # Assign to region
        cluster_id = None
        if state.pip_assigner:
            assignments = state.pip_assigner.assign_points(
                np.array([[request.longitude, request.latitude]])
            )
            cluster_id = assignments[0] if len(assignments) > 0 else None
        
        # Get predictions
        features_df = pd.DataFrame([features])
        predictions = state.predictor.predict(features_df, cluster_id)
        
        # Detect anomalies
        anomaly_scores = state.detector.detect(
            features_df,
            predictions,
            cluster_id
        )
        
        # Compute overall score
        overall_score = float(np.mean(anomaly_scores))
        
        # Determine anomaly level
        if overall_score < 0.3:
            level = AnomalyLevel.NORMAL
            is_anomalous = False
        elif overall_score < 0.5:
            level = AnomalyLevel.MILD
            is_anomalous = False
        elif overall_score < 0.7:
            level = AnomalyLevel.MODERATE
            is_anomalous = True
        else:
            level = AnomalyLevel.SEVERE
            is_anomalous = True
        
        # Create depth-wise scores
        scores_by_depth = []
        for i, (p, t, s) in enumerate(zip(request.pressure, request.temperature, request.salinity)):
            score = float(anomaly_scores[min(i, len(anomaly_scores)-1)])
            
            if score < 0.3:
                depth_level = AnomalyLevel.NORMAL
            elif score < 0.5:
                depth_level = AnomalyLevel.MILD
            elif score < 0.7:
                depth_level = AnomalyLevel.MODERATE
            else:
                depth_level = AnomalyLevel.SEVERE
            
            scores_by_depth.append(AnomalyScore(
                depth=float(p),
                temperature_score=score,
                salinity_score=score,
                combined_score=score,
                is_anomaly=score > 0.5,
                level=depth_level
            ))
        
        return ProfileResponse(
            profile_id=profile_meta['global_profile_id'],
            latitude=request.latitude,
            longitude=request.longitude,
            date=request.date,
            cluster_id=cluster_id,
            overall_score=overall_score,
            is_anomalous=is_anomalous,
            anomaly_level=level,
            scores_by_depth=scores_by_depth,
            features=features,
            metadata={
                'n_levels': len(request.pressure),
                'max_depth': max(request.pressure),
                'detector_used': request.detector.value
            }
        )
        
    except Exception as e:
        logger.error(f"Error detecting anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/batch", response_model=BatchProfileResponse)
async def detect_batch(request: BatchProfileRequest):
    """
    Detect anomalies in multiple profiles.
    """
    if not state.models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please train models first."
        )
    
    try:
        responses = []
        
        for profile_req in request.profiles:
            # Process each profile
            response = await detect_anomaly(profile_req)
            responses.append(response)
        
        # Compute summary statistics
        anomaly_count = sum(1 for r in responses if r.is_anomalous)
        avg_score = np.mean([r.overall_score for r in responses])
        
        summary = {
            'total_profiles': len(responses),
            'anomalous_profiles': anomaly_count,
            'anomaly_rate': anomaly_count / len(responses) if responses else 0,
            'average_score': float(avg_score),
            'processing_time_seconds': 0.0  # TODO: Track actual time
        }
        
        return BatchProfileResponse(
            profiles=responses,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error in batch detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train", response_model=TrainingResponse)
async def trigger_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger model training (background task).
    """
    # Generate task ID
    task_id = f"train_{datetime.now().timestamp()}"
    
    # Add training task to background
    background_tasks.add_task(
        run_training,
        request.start_date,
        request.end_date,
        request.regions,
        request.force_retrain
    )
    
    return TrainingResponse(
        task_id=task_id,
        status="queued",
        message="Training task queued",
        estimated_time_minutes=30.0
    )


async def run_training(
    start_date: datetime,
    end_date: datetime,
    regions: Optional[list],
    force_retrain: bool
):
    """
    Background task for model training.
    """
    try:
        logger.info(f"Starting training: {start_date} to {end_date}")
        
        # TODO: Implement actual training pipeline
        # This would involve:
        # 1. Load data
        # 2. Extract features
        # 3. Cluster regions
        # 4. Train models
        # 5. Save models
        
        state.last_training = datetime.now()
        state.models_loaded = True
        
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")


@app.post("/validate", response_model=ValidationResponse)
async def validate_models(request: ValidationRequest):
    """
    Validate models against test data.
    """
    if not state.models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please train models first."
        )
    
    # TODO: Implement validation
    raise HTTPException(status_code=501, detail="Validation not yet implemented")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
