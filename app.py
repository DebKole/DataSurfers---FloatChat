from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from main import AgentState,add_query,model
from float_location_service import FloatLocationService
import warnings
import os
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from io import BytesIO

warnings.filterwarnings("ignore")
load_dotenv()

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React app
        "http://localhost:8081",  # Expo web app
        "http://127.0.0.1:8081",  # Expo web app (alternative)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize float location service
float_service = FloatLocationService()

# Database setup for trend analysis
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "floatchat_argo")
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



# Trend Analysis API Endpoints

@app.get("/api/ts_curve", response_model=ProfilesResponse)
def ts_curve(float_id: str, limit: int = 200):
    """Get temperature-salinity curve for a float"""
    try:
        df = load_profile_data(float_id, limit)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data for this float_id")

        result = argo_ts_curve(df.to_dict("records"), show_plot=False)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_ts_png")
def compare_ts_png(float_id_a: str, float_id_b: str, limit: int = 200):
    """Return a PNG image comparing TS profiles for two floats."""
    try:
        df_a = load_profile_data(float_id_a, limit)
        df_b = load_profile_data(float_id_b, limit)

        if df_a.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_a={float_id_a}")
        if df_b.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_b={float_id_b}")

        result = argo_comparison_tool(
            datasets=[df_a.to_dict("records"), df_b.to_dict("records")],
            labels=[float_id_a, float_id_b],
            variable="temperature",
            axis_var="salinity",
        )

        profiles = result.get("profiles", [])
        if len(profiles) < 2:
            raise HTTPException(status_code=404, detail="Insufficient comparison data")

        # measurements[0] is stats; subsequent have curve data
        def extract_curve(profile):
            curve = []
            for m in profile.get("measurements", [])[1:]:
                s = m.get("salinity")
                t = m.get("temperature")
                if s is not None and t is not None:
                    curve.append((float(s), float(t)))
            return curve

        curve_a = extract_curve(profiles[0])
        curve_b = extract_curve(profiles[1])

        if not curve_a or not curve_b:
            raise HTTPException(status_code=404, detail="No curve data to plot")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([p[0] for p in curve_a], [p[1] for p in curve_a], "b-", linewidth=2.0, label=float_id_a)
        ax.plot([p[0] for p in curve_b], [p[1] for p in curve_b], "r-", linewidth=2.0, label=float_id_b)
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("TS Comparison")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend()

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        return Response(content=buf.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_td_png")
def compare_td_png(float_id_a: str, float_id_b: str, limit: int = 200):
    """Return a PNG image comparing TD profiles for two floats (temperature vs pressure)."""
    try:
        df_a = load_profile_data(float_id_a, limit)
        df_b = load_profile_data(float_id_b, limit)

        if df_a.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_a={float_id_a}")
        if df_b.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_b={float_id_b}")

        result = argo_comparison_tool(
            datasets=[df_a.to_dict("records"), df_b.to_dict("records")],
            labels=[float_id_a, float_id_b],
            variable="temperature",
            axis_var="pressure",
        )

        profiles = result.get("profiles", [])
        if len(profiles) < 2:
            raise HTTPException(status_code=404, detail="Insufficient comparison data")

        def extract_curve(profile):
            curve = []
            for m in profile.get("measurements", [])[1:]:
                p = m.get("pressure")
                t = m.get("temperature")
                if p is not None and t is not None:
                    curve.append((float(p), float(t)))
            return curve

        curve_a = extract_curve(profiles[0])
        curve_b = extract_curve(profiles[1])

        if not curve_a or not curve_b:
            raise HTTPException(status_code=404, detail="No curve data to plot")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([p[0] for p in curve_a], [p[1] for p in curve_a], "b-", linewidth=2.0, label=float_id_a)
        ax.plot([p[0] for p in curve_b], [p[1] for p in curve_b], "r-", linewidth=2.0, label=float_id_b)
        ax.set_xlabel("Pressure (dbar)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("TD Comparison")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend()

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        return Response(content=buf.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ts_curve_png")
def ts_curve_png(float_id: str, limit: int = 200):
    """Return a PNG image of the temperature–salinity (TS) profile for a float."""
    try:
        df = load_profile_data(float_id, limit)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data for this float_id")

        # Reuse TS curve computation to get salinity and temperature arrays
        result = argo_ts_curve(df.to_dict("records"), show_plot=False)
        profiles = result.get("profiles", [])
        if not profiles:
            raise HTTPException(status_code=404, detail="No TS data for this float_id")

        measurements = profiles[0].get("measurements", [])
        if not measurements:
            raise HTTPException(status_code=404, detail="No TS measurements for this float_id")

        sal = [m.get("salinity") for m in measurements if m.get("salinity") is not None]
        temps = [m.get("temperature") for m in measurements if m.get("temperature") is not None]

        if not sal or not temps or len(sal) != len(temps):
            raise HTTPException(status_code=404, detail="Insufficient TS data to plot")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(sal, temps, "b-", linewidth=2.0)
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title(f"Temperature–Salinity Profile for {float_id}")
        ax.grid(True, alpha=0.3, linestyle="--")

        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        return Response(content=buf.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/td_curve_png")
def td_curve_png(float_id: str, limit: int = 200):
    """Return a PNG image of the temperature–depth profile for a float."""
    try:
      df = load_profile_data(float_id, limit)
      if df.empty:
          raise HTTPException(status_code=404, detail="No data for this float_id")

      # Reuse TD curve computation to get depth and temperature arrays
      result = argo_td_curve(df.to_dict("records"), show_plot=False)
      profiles = result.get("profiles", [])
      if not profiles:
          raise HTTPException(status_code=404, detail="No TD data for this float_id")

      measurements = profiles[0].get("measurements", [])
      if not measurements:
          raise HTTPException(status_code=404, detail="No TD measurements for this float_id")

      depths = [m.get("depth") for m in measurements if m.get("depth") is not None]
      temps = [m.get("temperature") for m in measurements if m.get("temperature") is not None]

      if not depths or not temps or len(depths) != len(temps):
          raise HTTPException(status_code=404, detail="Insufficient TD data to plot")

      # Create matplotlib figure
      fig, ax = plt.subplots(figsize=(6, 4))
      ax.plot(temps, depths, "r-", linewidth=2.0)
      ax.set_xlabel("Temperature (°C)")
      ax.set_ylabel("Depth (m)")
      ax.set_title(f"Temperature–Depth Profile for {float_id}")
      ax.grid(True, alpha=0.3, linestyle="--")
      ax.invert_yaxis()  # depth increases downward

      buf = BytesIO()
      fig.tight_layout()
      fig.savefig(buf, format="png")
      plt.close(fig)
      buf.seek(0)

      return Response(content=buf.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/td_curve", response_model=ProfilesResponse)
def td_curve(float_id: str, limit: int = 200):
    """Get temperature-depth curve for a float"""
    try:
        df = load_profile_data(float_id, limit)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data for this float_id")

        result = argo_td_curve(df.to_dict("records"), show_plot=False)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_td", response_model=ProfilesResponse)
def compare_td(float_id_a: str, float_id_b: str, limit: int = 200):
    """Compare temperature-pressure profiles for two floats"""
    try:
        df_a = load_profile_data(float_id_a, limit)
        df_b = load_profile_data(float_id_b, limit)

        if df_a.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_a={float_id_a}")
        if df_b.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_b={float_id_b}")

        result = argo_comparison_tool(
            datasets=[df_a.to_dict("records"), df_b.to_dict("records")],
            labels=[float_id_a, float_id_b],
            variable="temperature",
            axis_var="pressure",
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_ts", response_model=ProfilesResponse)
def compare_ts(float_id_a: str, float_id_b: str, limit: int = 200):
    """Compare temperature-salinity profiles for two floats"""
    try:
        df_a = load_profile_data(float_id_a, limit)
        df_b = load_profile_data(float_id_b, limit)

        if df_a.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_a={float_id_a}")
        if df_b.empty:
            raise HTTPException(status_code=404, detail=f"No data for float_id_b={float_id_b}")

        result = argo_comparison_tool(
            datasets=[df_a.to_dict("records"), df_b.to_dict("records")],
            labels=[float_id_a, float_id_b],
            variable="temperature",
            axis_var="salinity",
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
