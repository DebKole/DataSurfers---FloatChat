# Dashboard Filter & Metadata Implementation

## Overview
Added comprehensive filtering and metadata display capabilities to the Dashboard component, inspired by the Argo Fleet Monitoring interface.

## New Components

### 1. FilterSidebar Component (`src/components/FilterSidebar.js`)
- **Features:**
  - Slide-out sidebar with filters
  - Filter categories: Status, Year of Deployment, Basin, Data Mode
  - Real-time filter counts from database
  - Clear all filters functionality
  - Active filter badge indicator
  - Smooth animations and transitions

- **Usage:**
  ```jsx
  <FilterSidebar
    onFilterChange={handleFilterChange}
    isOpen={filterOpen}
    onToggle={() => setFilterOpen(!filterOpen)}
  />
  ```

### 2. FloatMetadata Component (`src/components/FloatMetadata.js`)
- **Features:**
  - Tabbed interface (Main Information / All Metadata)
  - Three main sections:
    - About Float (WMO, platform info, sensors)
    - Deployment (launch date, location, project)
    - Cycle Activity (status, age, last profile)
  - Responsive grid layout
  - Highlight active status
  - Raw metadata view

- **Usage:**
  ```jsx
  <FloatMetadata floatId={selectedFloat} />
  ```

## Backend API Endpoints

### 1. Get Float Metadata
```
GET /api/floats/{float_id}/metadata
```
Returns detailed metadata including:
- About section (WMO, platform, sensors)
- Deployment information
- Cycle activity
- Raw metadata

### 2. Get Filter Options
```
GET /api/metadata/filters
```
Returns available filter options with counts:
- Status (Active/Inactive)
- Year of Deployment
- Basin (Indian Ocean, Pacific Ocean, Atlantic Ocean)
- Data Mode
- Country (placeholder)
- Telecom (placeholder)

## Dashboard Updates

### New Features:
1. **Filter Toggle Button** - Fixed position in top-right corner
2. **Show/Hide Metadata Button** - Toggle metadata display for selected float
3. **Filter Integration** - Filters can be applied to float list (backend support ready)
4. **Metadata Display** - Rich metadata view with tabbed interface

### UI Improvements:
- Consistent styling with existing dashboard theme
- Smooth animations and transitions
- Responsive layout
- Dark theme with blue accents
- Improved visual hierarchy

## Styling

All components use consistent styling:
- Dark blue gradient backgrounds
- Blue accent colors (#3182ce)
- Smooth transitions
- Custom scrollbars
- Hover effects
- Responsive design

## How to Use

1. **Open Filters:**
   - Click the "Filters" button in the top-right corner
   - Select desired filter options
   - Filters show count of matching floats
   - Click "Clear All Filters" to reset

2. **View Metadata:**
   - Select a float from the list
   - Click "Show Metadata" button
   - Switch between "Main Information" and "All Metadata" tabs
   - View detailed float information

3. **Filter Floats:**
   - Use the search box to filter by float ID
   - Apply metadata filters for advanced filtering
   - Filtered results update automatically

## Future Enhancements

1. **Backend Filter Integration:**
   - Connect filter selections to backend queries
   - Implement filtered float list endpoint
   - Add pagination for large result sets

2. **Additional Metadata:**
   - Country information
   - Telecom system details
   - Sensor specifications
   - Historical trajectory data

3. **Export Features:**
   - Export metadata to CSV/JSON
   - Download filtered float lists
   - Generate reports

4. **Advanced Filters:**
   - Date range filters
   - Geographic region filters
   - Parameter availability filters
   - Quality control filters
