# Filter and Download Functionality Update

## Overview
Implemented working filters with real database queries and added chart download functionality to the Dashboard.

## Changes Made

### 1. Backend API Updates (`app.py`)

#### Enhanced `/api/floats` Endpoint
Now supports real filtering with query parameters:
- `year` - Filter by deployment year (e.g., 2021, 2022, 2023, 2024, 2025)
- `basin` - Filter by ocean basin (Indian Ocean, Pacific Ocean, Atlantic Ocean)
- `data_mode` - Filter by data mode (R, A, D, etc.)
- `start_date` - Filter floats with data after this date (YYYY-MM-DD)
- `end_date` - Filter floats with data before this date (YYYY-MM-DD)

**Example:**
```
GET /api/floats?year=2025&basin=Indian Ocean&limit=1000
```

The endpoint builds dynamic SQL WHERE clauses based on provided filters and queries the actual database.

#### Metadata Endpoints
- `/api/floats/{float_id}/metadata` - Returns real metadata from database
- `/api/metadata/filters` - Returns available filter options with actual counts from database

**Note on Metadata:** The metadata is partially real (from database) and partially placeholder:
- **Real data:** float_id, cycle_number, datetime, latitude, longitude, project_name, institution, data_mode, measurement_count
- **Placeholder data:** ship, cruise, principal investigator, PTT, serial number (these fields aren't in the current database schema)

### 2. Frontend Filter Updates

#### FilterSidebar Component (`src/components/FilterSidebar.js`)
Added:
- **Date Range Filters** - Start and end date inputs for temporal filtering
- Proper state management for date filters
- Updated clear filters to include date fields
- Better active filter detection

#### Dashboard Component (`src/components/Dashboard.js`)
- Filters now trigger actual API calls with query parameters
- `loadFloats()` function builds URLSearchParams from active filters
- useEffect dependency on `activeFilters` triggers reload when filters change
- Supports multiple filter combinations

### 3. Chart Download Functionality

#### PlotProfile Component (`src/components/PlotProfile.js`)
Added:
- **Download CSV Button** - Positioned in top-right corner of each chart
- Exports chart data to CSV format with columns: X-axis, Y-axis, Cycle
- Filename includes chart type (e.g., `Float_1901514_TS_Curve_data.csv`)
- Styled button with hover effects matching the dashboard theme

**CSV Format:**
```csv
Salinity (PSU),Temperature (°C),Cycle
34.5,15.2,1
34.6,15.3,1
...
```

### 4. Database Query Details

The filters work by querying the `argo_profiles` table with dynamic WHERE clauses:

**Year Filter:**
```sql
EXTRACT(YEAR FROM datetime) = 2025
```

**Basin Filter (Geographic):**
- Indian Ocean: `longitude BETWEEN 20 AND 120`
- Pacific Ocean: `longitude BETWEEN -180 AND -60 OR longitude BETWEEN 120 AND 180`
- Atlantic Ocean: `longitude BETWEEN -60 AND 20`

**Date Range:**
```sql
datetime >= '2025-01-01' AND datetime <= '2025-12-31'
```

## Current Data Scope

Based on your database configuration:
- **Primary Database:** `argo_indian_ocean_25` (2025 data)
- **Available Databases:** 2021, 2022, 2023, 2024, 2025
- **Current Dashboard:** Shows floats from 2025 by default

The floats you're seeing are indeed from 2025 because:
1. The default database is `argo_indian_ocean_25`
2. The `/api/floats` endpoint queries this database
3. Most recent data is from January 2025

## How to Access Multi-Year Data

To see floats from other years, you can:

1. **Use Year Filter** - Select different years in the filter sidebar
2. **Use Date Range** - Set start_date to earlier years (e.g., 2021-01-01)
3. **Backend Query** - The system can query across multiple databases using the multi-year routes

## Testing the Filters

1. **Open Dashboard** - Navigate to the dashboard
2. **Click Filter Button** - Top-right corner "⚙️ Filters"
3. **Select Filters:**
   - Choose a year (2021-2025)
   - Select a basin (Indian Ocean, Pacific Ocean, Atlantic Ocean)
   - Set date range
   - Pick data mode
4. **View Results** - Float list updates automatically
5. **Clear Filters** - Click "Clear All Filters" to reset

## Testing Chart Download

1. **Select a Float** - Click any float from the list
2. **View Charts** - TS Curve, TD Profile, TP Curve appear
3. **Download** - Click "📥 Download CSV" button on any chart
4. **Check File** - CSV file downloads with chart data

## Known Limitations

1. **Multiple Filter Values** - Currently only uses first selected value for each filter category (can be enhanced to support multiple)
2. **Metadata Completeness** - Some metadata fields are placeholders (ship, cruise, PI)
3. **Cross-Database Queries** - Filters currently query single database; can be enhanced to query across all year databases
4. **Country/Telecom Filters** - Not yet implemented (no data in current schema)

## Future Enhancements

1. **Multi-Value Filters** - Support selecting multiple years, basins, etc.
2. **Advanced Metadata** - Add more real metadata fields from NetCDF files
3. **Export Options** - Add PNG/SVG export for charts
4. **Filter Presets** - Save and load filter combinations
5. **Cross-Database Filtering** - Query all year databases simultaneously
6. **Performance** - Add caching for filter options and results
