# Anomaly Detection Module Implementation Guide

This guide outlines the step-by-step process to implement and deploy the Argo Anomaly Detection System.

## Phase 1: Environment & Setup

1.  **Prerequisites**:
    *   Python 3.9+
    *   PostgreSQL (with PostGIS extension)
    *   Docker & Docker Compose

2.  **Installation**:
    *   Clone the repository.
    *   Create a virtual environment: `python -m venv venv`.
    *   Install dependencies: `pip install -r requirements.txt`.
    *   Install system libraries: `libomp` (for XGBoost/LightGBM on macOS).

3.  **Configuration**:
    *   Copy `.env.example` to `.env` and set database credentials.
    *   Review `config/config.yaml` to adjust paths, date ranges, and model parameters.

## Phase 2: Data Pipeline

1.  **Data Ingestion**:
    *   Ensure raw Argo data is available (CSV or Database).
    *   Use `data/loader.py` to ingest profiles and measurements.
    *   **Action**: Run data loading scripts to populate your local environment or database.

2.  **Feature Engineering**:
    *   Compute oceanographic features (Density, MLD, Spice) using `features/oceanographic.py`.
    *   Compute temporal features (Seasonality, Trends) using `features/temporal.py`.
    *   **Action**: Run the feature engineering pipeline to create a feature matrix.

## Phase 3: Regional Clustering

1.  **Cluster Definition**:
    *   Use `clustering/clusterer.py` to group profiles based on physical properties (Temp/Salinity/Location).
    *   The system uses GMM (Gaussian Mixture Models) to define soft clusters.

2.  **Polygon Generation**:
    *   Convert clusters into geographic regions using `clustering/polygons.py`.
    *   This generates GeoJSON boundaries for each regime.
    *   **Action**: Run the clustering pipeline to generate `artifacts/polygons/`.

## Phase 4: Model Training

1.  **Regional Training**:
    *   Train separate regression models for each region using `models/trainer.py`.
    *   Models predict expected Temperature and Salinity at given depths.
    *   Supported algorithms: XGBoost, LightGBM, or Scikit-Learn GradientBoosting.

2.  **Validation**:
    *   Evaluate model performance using RMSE and R² metrics.
    *   **Action**: Run `pipeline/train_and_detect.py` (or the training segment) to build models in `artifacts/models/`.

## Phase 5: Anomaly Detection

1.  **Detection Logic**:
    *   Compare observed values vs. model predictions.
    *   Calculate residuals and apply thresholds.
    *   Use `anomaly/detectors.py` for ensemble detection (Residuals + Isolation Forest).

2.  **Scoring & Fusion**:
    *   Combine scores from multiple detectors using `anomaly/fusion.py`.
    *   Assign anomaly levels (Info, Warning, Critical).

## Phase 6: Deployment & Usage

1.  **API Deployment**:
    *   Start the FastAPI server: `python api/app.py`.
    *   Endpoints available at `http://localhost:8000`.

2.  **Automated Pipeline**:
    *   Schedule `pipeline/train_and_detect.py` for periodic runs.

3.  **Monitoring**:
    *   Check logs in `logs/` directory.
    *   Review results in `artifacts/results/`.
