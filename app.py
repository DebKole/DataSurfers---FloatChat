from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from main import AgentState,add_query,model
from float_location_service import FloatLocationService
from float_chat_mcp.data_access_tools.data_access_orchestrator import DataAccessOrchestrator
from float_chat_mcp.data_access_tools.db_executor_tool import DatabaseExecutorTool
import warnings
import os
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, date
import math

try:
    import numpy as np  # optional, if available we’ll use for type checks
except Exception:
    np = None

warnings.filterwarnings("ignore")
load_dotenv()

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize float location service
float_service = FloatLocationService()
orchestrator = DataAccessOrchestrator(use_gemini=True, enable_cache=True)
db_executor = DatabaseExecutorTool(enable_cache=True)

# Database setup for trend analysis
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "argo_db")
DB_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"
print(DB_URL)
engine = create_engine(DB_URL)

# Import MCP tool functions
from float_chat_mcp.analysis_tools import server
argo_ts_curve = server.argo_ts_curve.fn
argo_td_curve = server.argo_td_curve.fn
argo_temp_trend = server.argo_temp_trend.fn
argo_comparison_tool = server.argo_comparison_tool.fn


class QueryRequest(BaseModel):
    query: str


class ProfilesResponse(BaseModel):
    profiles: List[Dict[str, Any]]


def load_profile_data(float_id: str, limit: int = 200) -> pd.DataFrame:
    """Load profile data from database for a given float_id"""
    query = f"""
    SELECT
        p.float_id,
        p.global_profile_id,
        m.level,
        m.pressure,
        m.temperature,
        m.salinity,
        m.latitude,
        m.longitude,
        m.datetime
    FROM argo_profiles p
    JOIN argo_measurements m
        ON m.global_profile_id = p.global_profile_id
    WHERE p.float_id = '{float_id}'
    ORDER BY p.global_profile_id, m.level
    LIMIT {limit};
    """
    return pd.read_sql(query, engine)


# Ensure responses are JSON-serializable by converting common non-JSON types
def _to_jsonable(obj):
    # primitives
    if obj is None or isinstance(obj, (bool, int, float, str)):
        # Handle NaN/Inf which json.dumps cannot encode when allow_nan=False
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    # dates
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # pandas
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, pd.Series):
        return _to_jsonable(obj.to_dict())
    if isinstance(obj, pd.DataFrame):
        return [_to_jsonable(r) for r in obj.to_dict(orient="records")]

    # numpy
    if np is not None:
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return [_to_jsonable(x) for x in obj.tolist()]

    # mappings and iterables
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(x) for x in list(obj)]

    # fallback to string representation
    try:
        return str(obj)
    except Exception:
        return None


@app.get("/")
async def root():
    return {"message": "FloatChat server is running", "version": "1.0.0"}

@app.get("/api/execute_query")
async def api_execute_query(q: str = Query(..., description="Natural language query")):
    """Execute a natural-language query via the orchestrator and return its result."""
    try:
        result = orchestrator.execute_query(q)
        return _to_jsonable(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dataset-info")
async def get_dataset_info():
    """Basic dataset info from database statistics."""
    try:
        stats = db_executor.get_database_stats(database="main")
        return _to_jsonable({"status": 200, "data": stats.get("data", [])})
    except Exception as e:
        return {"status": 500, "error": str(e)}

@app.post("/")
async def query_answer(req: QueryRequest):
    state = add_query(req.query)
    result = model.invoke(state)
    ans = result["answers"][-1].content
    
    # Include additional data if it was a data-driven response
    response_data = {
        "status": 201,
        "message": ans,
        "query_type": result.get("data_response", {}).get("query_type", "general"),
        "has_data": result.get("use_data", False),
        "show_map": result.get("show_map", False)
    }
    
    # Add table data for frontend display
    if result.get("table_data") and result["table_data"].get("rows"):
        response_data["table_data"] = result["table_data"]
    
    # Add map data if available AND non-empty; otherwise, do not trigger map
    if result.get("show_map", False):
        raw_map = result.get("map_data", {})
        has_points = False
        try:
            if isinstance(raw_map, dict) and isinstance(raw_map.get("points"), list):
                has_points = len(raw_map.get("points", [])) > 0
            elif isinstance(raw_map, list):
                has_points = len(raw_map) > 0
        except Exception:
            has_points = False

        if has_points:
            response_data["show_map"] = True
            response_data["map_data"] = raw_map
        else:
            response_data["show_map"] = False
    
    # Ensure JSON serializable
    return _to_jsonable(response_data)


@app.get("/floats/indian-ocean")
async def get_indian_ocean_floats(
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get all active floats in the Indian Ocean region from January 2025 data"""
    try:
        floats = float_service.get_indian_ocean_floats(limit=limit)
        return {
            "status": 200,
            "count": len(floats),
            "floats": floats,
            "region": "Indian Ocean",
            "bounds": {
                "lat": [-40, 30],
                "lng": [20, 120]
            }
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e),
            "floats": []
        }


@app.get("/floats/radius")
async def get_floats_in_radius(
    lat: float = Query(..., description="Center latitude"),
    lon: float = Query(..., description="Center longitude"),
    radius: float = Query(default=10, ge=1, le=20000, description="Radius in kilometers"),
    limit: int = Query(default=50, ge=1, le=500)
):
    """Get floats within a specified radius from a center point"""
    try:
        floats = float_service.get_floats_in_radius(
            center_lat=lat,
            center_lon=lon,
            radius_km=radius,
            limit=limit
        )
        return {
            "status": 200,
            "count": len(floats),
            "floats": floats,
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e),
            "floats": []
        }


@app.get("/floats/all")
async def get_all_floats(
    limit: int = Query(default=100, ge=1, le=500)
):
    """Get all active floats from January 2025 data"""
    try:
        floats = float_service.get_all_active_floats(limit=limit)
        return {
            "status": 200,
            "count": len(floats),
            "floats": floats,
            "data_period": "January 2025"
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e),
            "floats": []
        }


@app.get("/floats/{float_id}")
async def get_float_details(
    float_id: str,
    min_depth: float = Query(default=0, ge=0),
    max_depth: float = Query(default=2000, le=6000)
):
    """Get detailed information for a specific float including measurements"""
    try:
        float_data = float_service.get_float_with_measurements(
            float_id=float_id,
            depth_range=(min_depth, max_depth)
        )
        
        if not float_data:
            return {
                "status": 404,
                "error": f"Float {float_id} not found in January 2025 data"
            }
        
        return {
            "status": 200,
            "float_id": float_id,
            "profile": float_data['profile'],
            "measurements": float_data['measurements'],
            "measurement_count": len(float_data['measurements'])
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e)
        }


@app.get("/floats/trajectories/radius")
async def get_trajectories_in_radius(
    lat: float = Query(..., description="Center latitude"),
    lon: float = Query(..., description="Center longitude"),
    radius: float = Query(default=10, ge=1, le=20000, description="Radius in kilometers"),
    limit: int = Query(default=50, ge=1, le=500)
):
    """Get trajectory data (all positions over time) for floats within radius"""
    try:
        trajectories = float_service.get_trajectories_in_radius(
            center_lat=lat,
            center_lon=lon,
            radius_km=radius,
            limit=limit
        )
        return {
            "status": 200,
            "count": len(trajectories),
            "trajectories": trajectories,
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e),
            "trajectories": []
        }




# Listing endpoints for floats and profiles
@app.get("/api/floats")
async def list_floats(limit: int = Query(default=1000, ge=1, le=5000), database: str = Query(default="main")):
    try:
        res = db_executor.get_distinct_floats(database=database, limit=limit)
        rows = res.get("data", [])
        floats = [r.get("float_id") or r.get("FLOAT_ID") for r in rows]
        floats = [str(f) for f in floats if f is not None]
        return {"status": 200, "count": len(floats), "floats": floats}
    except Exception as e:
        return {"status": 500, "error": str(e), "floats": []}


@app.get("/api/floats/{float_id}/profiles")
async def list_profiles(float_id: str, limit: int = Query(default=200, ge=1, le=2000), database: str = Query(default="main")):
    try:
        res = db_executor.get_profiles_list_by_float_id(float_id=float_id, database=database, limit=limit)
        return _to_jsonable({"status": 200, "profiles": res.get("data", [])})
    except Exception as e:
        return {"status": 500, "error": str(e), "profiles": []}


# Structured analysis endpoint (profile-specific)
@app.get("/api/analysis")
async def api_analysis(
    type: str = Query(..., description="Analysis type: ts_curve|td_curve|temp_trend|sal_trend|comparison|statistics"),
    float_id: str = Query(...),
    cycle_number: int | None = Query(default=None),
    database: str = Query(default="main")
):
    try:
        # Build structured plan for analysis
        intent = {
            "query_text": f"analysis {type} for float {float_id} cycle {cycle_number}",
            "entities": {"float_ids": [float_id], "regions": [], "parameters": [], "temporal": {}}
        }
        plan = {
            "strategy": "analysis",
            "analysis_type": type,
            "data_requirements": {"float_ids": [float_id], "regions": [], "parameters": [], "temporal": {}},
            "analysis_parameters": ({"cycle_number": cycle_number} if cycle_number is not None else {}),
            "database": database,
        }
        result = orchestrator._execute_analysis_strategy(plan, intent)  # internal call by design
        return _to_jsonable(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
