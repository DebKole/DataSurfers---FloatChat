"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DetectorType(str, Enum):
    """Available anomaly detector types."""
    MODEL_RESIDUAL = "model_residual"
    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    ENSEMBLE = "ensemble"


class AnomalyLevel(str, Enum):
    """Anomaly severity levels."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ProfileRequest(BaseModel):
    """Request model for single profile anomaly detection."""
    temperature: List[float] = Field(..., description="Temperature values (°C)")
    salinity: List[float] = Field(..., description="Salinity values (PSU)")
    pressure: List[float] = Field(..., description="Pressure values (dbar)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    date: datetime = Field(..., description="Profile date")
    detector: DetectorType = Field(
        DetectorType.ENSEMBLE,
        description="Detector type to use"
    )


class BatchProfileRequest(BaseModel):
    """Request model for batch profile processing."""
    profiles: List[ProfileRequest]
    detector: DetectorType = Field(
        DetectorType.ENSEMBLE,
        description="Detector type to use"
    )


class AnomalyScore(BaseModel):
    """Anomaly score for a single measurement."""
    depth: float = Field(..., description="Depth/pressure level")
    temperature_score: float = Field(..., description="Temperature anomaly score")
    salinity_score: float = Field(..., description="Salinity anomaly score")
    combined_score: float = Field(..., description="Combined anomaly score")
    is_anomaly: bool = Field(..., description="Whether this is flagged as anomaly")
    level: AnomalyLevel = Field(..., description="Anomaly severity level")


class ProfileResponse(BaseModel):
    """Response model for profile anomaly detection."""
    profile_id: Optional[str] = Field(None, description="Profile identifier")
    latitude: float
    longitude: float
    date: datetime
    cluster_id: Optional[int] = Field(None, description="Assigned cluster/region ID")
    overall_score: float = Field(..., description="Overall anomaly score (0-1)")
    is_anomalous: bool = Field(..., description="Whether profile is anomalous")
    anomaly_level: AnomalyLevel = Field(..., description="Overall anomaly level")
    scores_by_depth: List[AnomalyScore] = Field(
        ...,
        description="Anomaly scores at each depth level"
    )
    features: Optional[Dict[str, float]] = Field(
        None,
        description="Extracted features"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


class BatchProfileResponse(BaseModel):
    """Response model for batch processing."""
    profiles: List[ProfileResponse]
    summary: Dict[str, Any] = Field(
        ...,
        description="Summary statistics"
    )


class RegionInfo(BaseModel):
    """Information about a cluster/region."""
    cluster_id: int
    centroid_lat: float
    centroid_lon: float
    area_km2: float
    n_profiles: int
    model_trained: bool
    last_updated: Optional[datetime] = None


class SystemStatus(BaseModel):
    """System status information."""
    status: str = Field(..., description="System status (healthy/degraded/down)")
    version: str = Field(..., description="API version")
    models_loaded: bool = Field(..., description="Whether models are loaded")
    n_regions: int = Field(..., description="Number of regions/clusters")
    regions: List[RegionInfo] = Field(..., description="Region information")
    last_training: Optional[datetime] = Field(
        None,
        description="Last model training time"
    )


class TrainingRequest(BaseModel):
    """Request to trigger model training."""
    start_date: datetime = Field(..., description="Training data start date")
    end_date: datetime = Field(..., description="Training data end date")
    regions: Optional[List[int]] = Field(
        None,
        description="Specific regions to train (None = all)"
    )
    force_retrain: bool = Field(
        False,
        description="Force retraining even if models exist"
    )


class TrainingResponse(BaseModel):
    """Response from training request."""
    task_id: str = Field(..., description="Training task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    estimated_time_minutes: Optional[float] = Field(
        None,
        description="Estimated completion time"
    )


class ValidationRequest(BaseModel):
    """Request for model validation."""
    start_date: datetime
    end_date: datetime
    regions: Optional[List[int]] = None
    use_woa: bool = Field(True, description="Validate against WOA climatology")


class ValidationMetrics(BaseModel):
    """Validation metrics."""
    rmse: float
    mae: float
    r2: float
    skill_score: float
    anomaly_precision: float
    anomaly_recall: float
    anomaly_f1: float


class ValidationResponse(BaseModel):
    """Response from validation request."""
    overall_metrics: ValidationMetrics
    metrics_by_region: Dict[int, ValidationMetrics]
    n_profiles_validated: int
    validation_date: datetime


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    database_connected: bool
    models_loaded: bool
    api_version: str
