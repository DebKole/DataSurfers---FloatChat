"""
FastAPI routes for multi-year Argo float data access.
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from .data_access_tools.multi_year_db import multi_year_db

router = APIRouter(
    prefix="/api/multi-year",
    tags=["multi-year"],
    responses={404: {"description": "Not found"}},
)

@router.get("/floats/nearby")
async def get_floats_nearby(
    lat: float = Query(..., description="Center latitude"),
    lon: float = Query(..., description="Center longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers", ge=0.1, le=10000),
    limit: int = Query(100, description="Maximum number of results per year", ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """
    Get Argo floats within a specified radius of a point, across all available years.
    """
    try:
        results = multi_year_db.get_floats_in_region(lat, lon, radius_km, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/floats/{float_id}/timeseries")
async def get_float_timeseries(
    float_id: str,
    parameter: str = Query('temperature', description="Parameter to retrieve (e.g., 'temperature', 'salinity')"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """
    Get time series data for a specific float across all available years.
    """
    try:
        # Validate date formats
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
                
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        df = multi_year_db.get_float_timeseries(float_id, parameter, start_date, end_date)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for float {float_id}")
            
        # Convert to list of records for JSON serialization
        records = df.to_dict('records')
        
        # Add summary statistics
        stats = {
            'parameter': parameter,
            'num_measurements': len(records),
            'date_range': {
                'min': df['datetime'].min().isoformat(),
                'max': df['datetime'].max().isoformat()
            },
            'value_stats': {
                'min': float(df['value'].min()),
                'max': float(df['value'].max()),
                'mean': float(df['value'].mean()),
                'median': float(df['value'].median())
            } if not df.empty else {}
        }
        
        return {
            'float_id': float_id,
            'data': records,
            'stats': stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/floats/{float_id}/years")
async def get_float_years(float_id: str) -> Dict[str, Any]:
    """
    Get the years for which data is available for a specific float.
    """
    try:
        # Simple query to check which years have data for this float
        query = """
        SELECT DISTINCT EXTRACT(YEAR FROM datetime) as year
        FROM argo_measurements
        WHERE float_id = :float_id
        ORDER BY year
        """
        
        years = []
        for year, engine in multi_year_db.engines.items():
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(query), {'float_id': float_id})
                    year_data = [row[0] for row in result.fetchall()]
                    if year_data:
                        years.extend(year_data)
            except Exception as e:
                logger.warning(f"Error checking {year} database for float {float_id}: {e}")
        
        if not years:
            raise HTTPException(status_code=404, detail=f"No data found for float {float_id}")
            
        return {
            'float_id': float_id,
            'available_years': sorted(list(set(years))),  # Remove duplicates and sort
            'first_year': min(years),
            'last_year': max(years)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_summary_stats() -> Dict[str, Any]:
    """
    Get summary statistics across all years of data.
    """
    try:
        # This is a simple example - you might want to add more detailed statistics
        stats = {}
        
        for year, engine in multi_year_db.engines.items():
            try:
                # Get count of unique floats
                float_count = 0
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(DISTINCT float_id) FROM argo_measurements"))
                    float_count = result.scalar() or 0
                
                # Get count of profiles
                profile_count = 0
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(DISTINCT global_profile_id) FROM argo_measurements"))
                    profile_count = result.scalar() or 0
                
                # Get date range
                date_range = {}
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT MIN(datetime), MAX(datetime) FROM argo_measurements"))
                    min_date, max_date = result.fetchone()
                    if min_date and max_date:
                        date_range = {
                            'min': min_date.isoformat(),
                            'max': max_date.isoformat()
                        }
                
                stats[year] = {
                    'float_count': float_count,
                    'profile_count': profile_count,
                    'date_range': date_range
                }
                
            except Exception as e:
                logger.warning(f"Error getting stats for {year}: {e}")
                stats[year] = {'error': str(e)}
        
        return {
            'database_stats': stats,
            'available_years': list(multi_year_db.engines.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
