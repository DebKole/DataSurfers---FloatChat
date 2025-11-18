from fastapi import FastAPI, Query
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware


from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from main import AgentState,add_query,model
from float_location_service import FloatLocationService
import warnings
warnings.filterwarnings("ignore")
import os
load_dotenv()

app=FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize float location service
float_service = FloatLocationService()


class QueryRequest(BaseModel):
    query: str


@app.get("/")
async def root():
    return {"message": "FloatChat server is running", "version": "1.0.0"}

@app.get("/dataset-info")
async def get_dataset_info():
    """Get basic information about the loaded dataset."""
    from data_processor import ArgoDataProcessor
    processor = ArgoDataProcessor("argo_demo.csv")
    stats = processor.get_basic_stats()
    return {"status": 200, "data": stats}

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
    
    # Add map data if available
    if result.get("show_map", False):
        response_data["map_data"] = result.get("map_data", {})
    
    return response_data


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

