from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

from . import server  # relative import within analysis_tools  # your MCP tools

# Load environment variables
load_dotenv()

# Extract underlying Python functions from MCP tools
argo_ts_curve = server.argo_ts_curve.fn
argo_td_curve = server.argo_td_curve.fn
argo_temp_trend = server.argo_temp_trend.fn
argo_comparison_tool = server.argo_comparison_tool.fn

# --- DB setup using environment variables ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "floatchat_argo")

DB_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

app = FastAPI(title="Argo Trend API")

# Allow your dashboard origin to call this API (adjust origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProfilesResponse(BaseModel):
    profiles: List[Dict[str, Any]]


def load_profile_data(float_id: str, limit: int = 200) -> pd.DataFrame:
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


@app.get("/api/ts_curve", response_model=ProfilesResponse)
def ts_curve(float_id: str, limit: int = 200):
    try:
        df = load_profile_data(float_id, limit)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data for this float_id")

        result = argo_ts_curve(df.to_dict("records"), show_plot=False)
        return result  # { profiles: [...] }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/td_curve", response_model=ProfilesResponse)
def td_curve(float_id: str, limit: int = 200):
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
    """Compare temperature–pressure profiles for two floats.

    Uses argo_comparison_tool to build profiles for each float,
    with curve data along the pressure axis.
    """
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
        return result  # {"profiles": [...]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare_ts", response_model=ProfilesResponse)
def compare_ts(float_id_a: str, float_id_b: str, limit: int = 200):
    """Compare temperature–salinity (T–S) profiles for two floats.

    Uses argo_comparison_tool to build profiles for each float,
    with curve data along the salinity axis.
    """
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