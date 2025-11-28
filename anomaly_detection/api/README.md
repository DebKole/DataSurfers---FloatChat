# Argo Anomaly Detection API

REST API for real-time Argo profile anomaly detection.

## Quick Start

### Start the API Server

```bash
# From anomaly_detection directory
python api/app.py

# Or with uvicorn (recommended for production)
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access API Documentation

Open your browser to:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## API Endpoints

### Health & Status

#### GET /health
Health check endpoint.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-18T10:00:00",
  "database_connected": true,
  "models_loaded": true,
  "api_version": "1.0.0"
}
```

#### GET /status
Get detailed system status.

```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_loaded": true,
  "n_regions": 15,
  "regions": [...],
  "last_training": "2024-11-18T09:00:00"
}
```

### Anomaly Detection

#### POST /detect
Detect anomalies in a single profile.

```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": [20.0, 15.0, 10.0, 5.0],
    "salinity": [35.0, 35.2, 35.4, 35.6],
    "pressure": [0, 50, 100, 200],
    "latitude": 30.0,
    "longitude": -60.0,
    "date": "2019-01-15T00:00:00",
    "detector": "ensemble"
  }'
```

Response:
```json
{
  "profile_id": "api_1234567890",
  "latitude": 30.0,
  "longitude": -60.0,
  "date": "2019-01-15T00:00:00",
  "cluster_id": 5,
  "overall_score": 0.23,
  "is_anomalous": false,
  "anomaly_level": "normal",
  "scores_by_depth": [
    {
      "depth": 0,
      "temperature_score": 0.15,
      "salinity_score": 0.18,
      "combined_score": 0.17,
      "is_anomaly": false,
      "level": "normal"
    },
    ...
  ],
  "features": {...},
  "metadata": {...}
}
```

#### POST /detect/batch
Detect anomalies in multiple profiles.

```bash
curl -X POST http://localhost:8000/detect/batch \
  -H "Content-Type: application/json" \
  -d '{
    "profiles": [
      {
        "temperature": [20.0, 15.0, 10.0],
        "salinity": [35.0, 35.2, 35.4],
        "pressure": [0, 50, 100],
        "latitude": 30.0,
        "longitude": -60.0,
        "date": "2019-01-15T00:00:00"
      },
      ...
    ],
    "detector": "ensemble"
  }'
```

Response:
```json
{
  "profiles": [...],
  "summary": {
    "total_profiles": 100,
    "anomalous_profiles": 5,
    "anomaly_rate": 0.05,
    "average_score": 0.23,
    "processing_time_seconds": 2.5
  }
}
```

### Model Training

#### POST /train
Trigger model training (background task).

```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2019-01-01T00:00:00",
    "end_date": "2019-12-31T00:00:00",
    "regions": null,
    "force_retrain": false
  }'
```

Response:
```json
{
  "task_id": "train_1234567890",
  "status": "queued",
  "message": "Training task queued",
  "estimated_time_minutes": 30.0
}
```

## Python Client Example

```python
import requests
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

# Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Detect anomaly in single profile
profile_data = {
    "temperature": [20.0, 15.0, 10.0, 5.0],
    "salinity": [35.0, 35.2, 35.4, 35.6],
    "pressure": [0, 50, 100, 200],
    "latitude": 30.0,
    "longitude": -60.0,
    "date": "2019-01-15T00:00:00",
    "detector": "ensemble"
}

response = requests.post(f"{BASE_URL}/detect", json=profile_data)
result = response.json()

print(f"Anomaly Score: {result['overall_score']:.3f}")
print(f"Is Anomalous: {result['is_anomalous']}")
print(f"Level: {result['anomaly_level']}")
print(f"Cluster: {result['cluster_id']}")

# Batch processing
batch_data = {
    "profiles": [profile_data, profile_data],  # Multiple profiles
    "detector": "ensemble"
}

response = requests.post(f"{BASE_URL}/detect/batch", json=batch_data)
result = response.json()

print(f"Processed: {result['summary']['total_profiles']} profiles")
print(f"Anomalies: {result['summary']['anomalous_profiles']}")
print(f"Rate: {result['summary']['anomaly_rate']:.2%}")
```

## Detector Types

Available detector types:
- `model_residual`: Model-based residual detection
- `isolation_forest`: Isolation Forest detector
- `lof`: Local Outlier Factor detector
- `ensemble`: Multi-detector ensemble (recommended)

## Anomaly Levels

- `normal`: Score < 0.3 (no anomaly)
- `mild`: Score 0.3-0.5 (minor deviation)
- `moderate`: Score 0.5-0.7 (moderate anomaly)
- `severe`: Score > 0.7 (severe anomaly)

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `500`: Internal server error
- `503`: Service unavailable (models not loaded)

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Configuration

API configuration is loaded from `config/config.yaml`. Key settings:
- Model paths
- Feature engineering parameters
- Anomaly detection thresholds
- Database connections

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t argo-anomaly-api .

# Run container
docker run -p 8000:8000 argo-anomaly-api
```

### Using docker-compose

```bash
docker-compose up api
```

### Environment Variables

- `API_HOST`: Host to bind (default: 0.0.0.0)
- `API_PORT`: Port to bind (default: 8000)
- `API_WORKERS`: Number of workers (default: 4)
- `LOG_LEVEL`: Logging level (default: info)

## Performance

- Single profile detection: ~50-100ms
- Batch processing: ~20-50ms per profile
- Concurrent requests: Supports multiple workers

## Monitoring

The API includes:
- Health check endpoint for monitoring
- Detailed logging
- Request/response timing
- Error tracking

## Security

For production deployment:
- Enable HTTPS
- Add authentication (API keys, OAuth)
- Rate limiting
- Input validation (already included via Pydantic)

## Support

For issues or questions:
- Check API docs: http://localhost:8000/docs
- Review logs
- See main README.md
