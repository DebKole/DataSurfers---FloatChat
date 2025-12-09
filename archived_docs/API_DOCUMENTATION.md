# 🌊 Float Radius API Documentation

## For Frontend Team

This API provides endpoints to fetch Argo float data filtered by geographic radius. Use these endpoints to build your visualization.

---

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### 1. Get Floats Within Radius

**Endpoint:** `GET /floats/radius`

**Description:** Get all floats within a specified radius from a center point.

**Query Parameters:**
- `lat` (required): Center latitude (-90 to 90)
- `lon` (required): Center longitude (-180 to 180)
- `radius` (required): Radius in kilometers (1 to 10000)
- `limit` (optional): Maximum floats to return (default: 50, max: 200)

**Example Request:**
```bash
GET /floats/radius?lat=15&lon=70&radius=500&limit=50
```

**Example Response:**
```json
{
  "status": 200,
  "count": 8,
  "floats": [
    {
      "float_id": "5905521",
      "latitude": -8.2858,
      "longitude": 107.0376,
      "distance_km": 234.56,
      "datetime": "2025-01-31T23:56:21",
      "cycle_number": 99,
      "measurement_count": 982,
      "global_profile_id": 2354
    },
    ...
  ],
  "center": {
    "lat": 15.0,
    "lon": 70.0
  },
  "radius_km": 500
}
```

**Response Fields:**
- `float_id`: Unique float identifier
- `latitude`: Float latitude
- `longitude`: Float longitude
- `distance_km`: Distance from center point in kilometers
- `datetime`: Last measurement timestamp
- `cycle_number`: Float cycle number
- `measurement_count`: Number of measurements for this float
- `global_profile_id`: Database profile ID

---

### 2. Get All Indian Ocean Floats

**Endpoint:** `GET /floats/indian-ocean`

**Description:** Get all floats in the Indian Ocean region (no radius filter).

**Query Parameters:**
- `limit` (optional): Maximum floats to return (default: 50, max: 200)

**Example Request:**
```bash
GET /floats/indian-ocean?limit=100
```

**Example Response:**
```json
{
  "status": 200,
  "count": 100,
  "floats": [
    {
      "float_id": "5905521",
      "latitude": -8.2858,
      "longitude": 107.0376,
      "datetime": "2025-01-31T23:56:21",
      "cycle_number": 99,
      "measurement_count": 982,
      "global_profile_id": 2354
    },
    ...
  ],
  "region": "Indian Ocean",
  "bounds": {
    "lat": [-40, 30],
    "lng": [20, 120]
  }
}
```

---

### 3. Get All Active Floats

**Endpoint:** `GET /floats/all`

**Description:** Get all active floats from January 2025 data.

**Query Parameters:**
- `limit` (optional): Maximum floats to return (default: 100, max: 500)

**Example Request:**
```bash
GET /floats/all?limit=200
```

**Example Response:**
```json
{
  "status": 200,
  "count": 200,
  "floats": [...],
  "data_period": "January 2025"
}
```

---

### 4. Get Specific Float Details

**Endpoint:** `GET /floats/{float_id}`

**Description:** Get detailed information for a specific float including measurements.

**Path Parameters:**
- `float_id`: Float identifier (e.g., "5905521")

**Query Parameters:**
- `min_depth` (optional): Minimum depth in meters (default: 0)
- `max_depth` (optional): Maximum depth in meters (default: 2000)

**Example Request:**
```bash
GET /floats/5905521?min_depth=0&max_depth=1000
```

**Example Response:**
```json
{
  "status": 200,
  "float_id": "5905521",
  "profile": {
    "global_profile_id": 2354,
    "float_id": "5905521",
    "latitude": -8.2858,
    "longitude": 107.0376,
    "datetime": "2025-01-31T23:56:21",
    "cycle_number": 99,
    "measurement_count": 982
  },
  "measurements": [
    {
      "level": 0,
      "pressure": 5.0,
      "temperature": 28.5,
      "salinity": 34.2,
      "latitude": -8.2858,
      "longitude": 107.0376,
      "datetime": "2025-01-31T23:56:21"
    },
    ...
  ],
  "measurement_count": 100
}
```

---

## Error Responses

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["query", "radius"],
      "msg": "ensure this value is less than or equal to 10000",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Common Causes:**
- Radius > 10000km
- Invalid latitude/longitude
- Missing required parameters

### 404 Not Found
```json
{
  "status": 404,
  "error": "Float 9999999 not found in January 2025 data"
}
```

### 500 Internal Server Error
```json
{
  "status": 500,
  "error": "Database connection failed"
}
```

---

## Usage Examples

### JavaScript/React

```javascript
// Fetch floats within radius
const fetchFloatsInRadius = async (lat, lon, radius) => {
  const response = await fetch(
    `http://localhost:8000/floats/radius?lat=${lat}&lon=${lon}&radius=${radius}&limit=100`
  );
  const data = await response.json();
  return data.floats;
};

// Usage
const floats = await fetchFloatsInRadius(15.0, 70.0, 500);
console.log(`Found ${floats.length} floats`);
```

### Python

```python
import requests

# Fetch floats within radius
def get_floats_in_radius(lat, lon, radius, limit=100):
    url = f"http://localhost:8000/floats/radius"
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "limit": limit
    }
    response = requests.get(url, params=params)
    return response.json()

# Usage
data = get_floats_in_radius(15.0, 70.0, 500)
print(f"Found {data['count']} floats")
```

### cURL

```bash
# Get floats within 500km
curl "http://localhost:8000/floats/radius?lat=15&lon=70&radius=500&limit=50"

# Get all Indian Ocean floats
curl "http://localhost:8000/floats/indian-ocean?limit=100"

# Get specific float details
curl "http://localhost:8000/floats/5905521"
```

---

## Preset Center Points

### Indian Coast Regions

**Arabian Sea (West Coast):**
```
lat: 15.0, lon: 70.0
```

**Bay of Bengal (East Coast):**
```
lat: 15.0, lon: 85.0
```

**Mumbai Region:**
```
lat: 19.0, lon: 72.0
```

**Chennai Region:**
```
lat: 13.0, lon: 80.0
```

**Southern Tip (Near Sri Lanka):**
```
lat: 8.0, lon: 78.0
```

---

## Radius Recommendations

- **50-100km:** Very close to coast, few floats
- **200-500km:** Coastal region, moderate coverage
- **500-1000km:** Extended coastal zone, good coverage
- **1000-2000km:** Wide area, many floats
- **5000-10000km:** Entire ocean basin

---

## Data Characteristics

- **Total Floats:** 816 unique floats
- **Total Profiles:** 2,434 profiles
- **Date Range:** January 1-31, 2025
- **Region:** Indian Ocean
- **Geographic Bounds:**
  - Latitude: -68.18° to 23.98°
  - Longitude: 20.02° to 145.00°

---

## Performance Notes

- Queries with radius < 1000km: ~50-100ms
- Queries with radius > 1000km: ~100-200ms
- Limit parameter affects response size, not query speed
- Database has spatial indexes for fast geographic queries

---

## Rate Limiting

Currently no rate limiting. For production:
- Recommended: 100 requests/minute per IP
- Burst: 10 requests/second

---

## CORS

CORS is enabled for:
- `http://localhost:3000` (React dev server)

For production, update `app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    ...
)
```

---

## Testing

### Test Radius Endpoint
```bash
# Small radius (few floats)
curl "http://localhost:8000/floats/radius?lat=15&lon=70&radius=100"

# Medium radius (moderate floats)
curl "http://localhost:8000/floats/radius?lat=15&lon=70&radius=500"

# Large radius (many floats)
curl "http://localhost:8000/floats/radius?lat=15&lon=70&radius=2000"
```

### Expected Float Counts

From center (15°N, 70°E):
- 100km: ~2-3 floats
- 500km: ~8-15 floats
- 1000km: ~30-50 floats
- 2000km: ~60-80 floats
- 5000km: ~100+ floats

---

## Support

For issues or questions:
1. Check backend logs: `uvicorn app:app --reload`
2. Test API directly: `curl http://localhost:8000/floats/radius?lat=15&lon=70&radius=500`
3. Verify database: `python check_database_floats.py`

---

## Summary for Frontend Team

**What you need:**
1. Use `/floats/radius` endpoint with lat, lon, radius parameters
2. Display returned floats on map
3. Add UI controls for users to adjust radius
4. Handle loading states and errors

**What we provide:**
- Fast API with geographic filtering
- Distance calculations (Haversine formula)
- Real data from January 2025
- 816 floats across Indian Ocean

**Your responsibility:**
- Map visualization
- Radius slider/input UI
- Float markers and popups
- User interaction

---

**API is ready for integration!** 🚀
