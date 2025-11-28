# Argo Ocean Data Anomaly Detection System

A geographically-aware anomaly detection system for Argo float ocean profile data using regional clustering, distance-weighted modeling, and multi-detector fusion.

## Project Structure

```
anomaly_detection/
├── config/                 # Configuration files
│   ├── config.yaml        # Main configuration
│   └── regions.yaml       # Region-specific settings
├── data/                  # Data processing modules
│   ├── __init__.py
│   ├── loader.py          # Data loading from CSV/Postgres
│   └── validator.py       # Data validation
├── features/              # Feature engineering
│   ├── __init__.py
│   ├── engineer.py        # Feature computation
│   ├── oceanographic.py   # Ocean-specific features (GSW)
│   └── temporal.py        # Temporal features
├── clustering/            # Regional clustering
│   ├── __init__.py
│   ├── clusterer.py       # GMM/HDBSCAN clustering
│   ├── polygons.py        # Polygon generation (alpha shapes)
│   └── validator.py       # Cluster validation
├── geo/                   # Geospatial operations
│   ├── __init__.py
│   ├── pip_assign.py      # Point-in-polygon assignment
│   ├── distance_weights.py # Distance-based weighting
│   └── spatial_index.py   # R-tree spatial indexing
├── models/                # ML models
│   ├── __init__.py
│   ├── trainer.py         # Regional model training
│   ├── predictor.py       # Prediction interface
│   └── uncertainty.py     # Uncertainty quantification
├── anomaly/               # Anomaly detection
│   ├── __init__.py
│   ├── detectors.py       # Multi-detector implementation
│   ├── fusion.py          # Score fusion
│   └── calibration.py     # Threshold calibration
├── validation/            # Validation against external data
│   ├── __init__.py
│   ├── woa_validator.py   # World Ocean Atlas validation
│   └── metrics.py         # Evaluation metrics
├── api/                   # REST API
│   ├── __init__.py
│   ├── app.py             # FastAPI application
│   └── schemas.py         # Pydantic models
├── notebooks/             # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_clustering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_anomaly_detection.ipynb
├── pipeline/            # Pipeline scripts
│   ├── __init__.py
│   ├── quick_test.py      # Quick test script
│   └── train_and_detect.py # Full pipeline script
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_clustering.py
│   ├── test_anomaly.py
│   └── test_clustering_geo.py
├── artifacts/             # Model artifacts (gitignored)
│   ├── models/
│   ├── polygons/
│   └── scalers/
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker compose for services
└── README.md             # This file
```

## Installation

```bash
# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

## Quick Start

### 1. Run Quick Test
```bash
python pipeline/quick_test.py
```

### 2. Run Full Pipeline
```bash
python pipeline/train_and_detect.py --config config/config.yaml
```

### 3. Start API
```bash
python api/app.py
```

### 4. Interactive Menu
```bash
python run.py
```

## Configuration

Edit `config/config.yaml` to customize:
- Database connection
- Clustering parameters
- Model hyperparameters
- Anomaly detection thresholds

## API Usage

Start the API server:
```bash
uvicorn anomaly_detection.api.app:app --reload
```

Detect anomalies via API:
```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"latitude": -36.2, "longitude": 69.6, "temperature": [18.7, 18.7, ...], "salinity": [35.3, 35.4, ...], "pressure": [6.4, 10.4, ...]}'
```

## Development

Run tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=anomaly_detection --cov-report=html
```

## License

MIT
