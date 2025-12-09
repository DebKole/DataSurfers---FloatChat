# 🛤️ Trajectory API Documentation

## For Frontend Team - Map Trajectories

This API provides trajectory data (movement paths) for floats within a specified radius.

---

## Endpoint

### Get Trajectories Within Radius

**Endpoint:** `GET /floats/trajectories/radius`

**Description:** Get all positions over time for floats within a radius. Returns multiple points per float to show movement path.

**Query Parameters:**
- `lat` (required): Center latitude (-90 to 90)
- `lon` (required): Center longitude (-180 to 180)
- `radius` (required): Radius in kilometers (1 to 20,000)
- `limit` (optional): Maximum number of floats (default: 50, max: 500)

**Example Request:**
```bash
GET /floats/trajectories/radius?lat=15&lon=70&radius=500&limit=50
```

---

## Response Format

```json
{
  "status": 200,
  "count": 145,
  "trajectories": [
    {
      "profileId": 2354,
      "lat": -8.2858,
      "lon": 107.0376,
      "floatId": "5905521",
      "cycleNumber": 99,
      "datetime": "2025-01-31T23:56:21"
    },
    {
      "profileId": 2355,
      "lat": -8.2901,
      "lon": 107.0412,
      "floatId": "5905521",
      "cycleNumber": 100,
      "datetime": "2025-01-30T12:34:56"
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

---

## Data Structure

### TrajectoryPoint Type

```typescript
type TrajectoryPoint = {
  profileId: string | number;  // Unique profile ID
  lat: number;                 // Latitude
  lon: number;                 // Longitude
  floatId?: string | number;   // Float identifier
  cycleNumber?: number;        // Cycle number
  datetime?: string;           // Timestamp (ISO format)
};
```

---

## How It Works

1. **Finds floats within radius** (using latest position)
2. **Gets ALL profiles for those floats** (entire movement history)
3. **Returns chronologically ordered points** per float
4. **Frontend draws lines** connecting points for each float

---

## Usage Example

### JavaScript/React

```javascript
const fetchTrajectories = async (lat, lon, radius) => {
  const response = await fetch(
    `http://localhost:8000/floats/trajectories/radius?lat=${lat}&lon=${lon}&radius=${radius}&limit=50`
  );
  const data = await response.json();
  return data.trajectories;
};

// Group by float to draw paths
const groupByFloat = (trajectories) => {
  const grouped = {};
  trajectories.forEach(point => {
    const floatId = point.floatId;
    if (!grouped[floatId]) {
      grouped[floatId] = [];
    }
    grouped[floatId].push(point);
  });
  return grouped;
};

// Usage
const trajectories = await fetchTrajectories(15.0, 70.0, 500);
const floatPaths = groupByFloat(trajectories);

// Draw each float's path
Object.entries(floatPaths).forEach(([floatId, points]) => {
  // points is array of positions for this float
  // Draw line connecting: points[0] -> points[1] -> points[2] -> ...
  drawPath(points);
});
```

### Drawing Trajectories with Leaflet

```javascript
import { Polyline } from 'react-leaflet';

// For each float, create a polyline
{Object.entries(floatPaths).map(([floatId, points]) => (
  <Polyline
    key={floatId}
    positions={points.map(p => [p.lat, p.lon])}
    color="blue"
    weight={2}
  />
))}
```

---

## Example Response Breakdown

For **2 floats** with **3 positions each**:

```json
{
  "trajectories": [
    // Float 5905521 - Position 1
    {"profileId": 2354, "lat": -8.28, "lon": 107.03, "floatId": "5905521", "datetime": "2025-01-29"},
    // Float 5905521 - Position 2
    {"profileId": 2355, "lat": -8.29, "lon": 107.04, "floatId": "5905521", "datetime": "2025-01-30"},
    // Float 5905521 - Position 3
    {"profileId": 2356, "lat": -8.30, "lon": 107.05, "floatId": "5905521", "datetime": "2025-01-31"},
    
    // Float 6903142 - Position 1
    {"profileId": 2357, "lat": -0.69, "lon": 77.99, "floatId": "6903142", "datetime": "2025-01-29"},
    // Float 6903142 - Position 2
    {"profileId": 2358, "lat": -0.70, "lon": 78.00, "floatId": "6903142", "datetime": "2025-01-30"},
    // Float 6903142 - Position 3
    {"profileId": 2359, "lat": -0.71, "lon": 78.01, "floatId": "6903142", "datetime": "2025-01-31"}
  ]
}
```

**Frontend groups by floatId:**
- Float 5905521: 3 points → Draw line through them
- Float 6903142: 3 points → Draw line through them

---

## Testing

### Test with cURL

```bash
# Get trajectories within 500km
curl "http://localhost:8000/floats/trajectories/radius?lat=15&lon=70&radius=500&limit=10"
```

### Expected Result

- Returns multiple points per float
- Points are ordered by datetime
- Each point has lat, lon, floatId
- Can draw lines connecting points for each float

---

## Data Characteristics

- **January 2025 data only**
- **Multiple profiles per float** (showing movement over time)
- **Chronologically ordered** (oldest to newest)
- **Grouped by float** (frontend responsibility)

---

## Performance

- **Small radius (100km):** ~10-30 trajectory points
- **Medium radius (500km):** ~50-150 trajectory points
- **Large radius (1000km):** ~200-500 trajectory points

Each float typically has 1-10 profiles in January 2025.

---

## Integration with Radius Slider

```javascript
const [radius, setRadius] = useState(500);
const [trajectories, setTrajectories] = useState([]);

// Fetch when radius changes
useEffect(() => {
  const fetchData = async () => {
    const data = await fetchTrajectories(15, 70, radius);
    setTrajectories(data);
  };
  fetchData();
}, [radius]);

// Slider
<input 
  type="range" 
  min="100" 
  max="2000" 
  value={radius}
  onChange={(e) => setRadius(e.target.value)}
/>
```

---

## Difference from `/floats/radius`

| Endpoint | Returns | Use Case |
|----------|---------|----------|
| `/floats/radius` | **Latest position** per float | Show current float locations |
| `/floats/trajectories/radius` | **All positions** per float | Show movement paths/trajectories |

---

## Summary for Frontend Team

**What you get:**
- Array of trajectory points
- Multiple points per float (showing movement)
- Ordered by time

**What you need to do:**
1. Group points by `floatId`
2. Draw lines connecting points for each float
3. Add to map with different colors per float
4. Update when radius slider changes

**API is ready!** 🚀

---

## Example Implementation

```javascript
// MapTrajectories.js
const MapTrajectories = ({ centerLat, centerLon, radius }) => {
  const [trajectories, setTrajectories] = useState([]);

  useEffect(() => {
    fetch(`http://localhost:8000/floats/trajectories/radius?lat=${centerLat}&lon=${centerLon}&radius=${radius}`)
      .then(r => r.json())
      .then(data => setTrajectories(data.trajectories));
  }, [centerLat, centerLon, radius]);

  // Group by float
  const floatPaths = trajectories.reduce((acc, point) => {
    if (!acc[point.floatId]) acc[point.floatId] = [];
    acc[point.floatId].push([point.lat, point.lon]);
    return acc;
  }, {});

  return (
    <MapContainer>
      {Object.entries(floatPaths).map(([floatId, positions]) => (
        <Polyline 
          key={floatId}
          positions={positions}
          color="blue"
        />
      ))}
    </MapContainer>
  );
};
```

---

**Your trajectory API is complete!** Hand this doc to the frontend team. ✅
