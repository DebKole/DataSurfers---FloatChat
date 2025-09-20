from fastapi import FastAPI
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware


from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from main import AgentState,add_query,model
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
    
    # Add structured data if available (for potential future visualization)
    if result.get("use_data") and "data" in result.get("data_response", {}):
        response_data["structured_data"] = result["data_response"]["data"]
    
    # Add map data if available
    if result.get("show_map", False):
        response_data["map_data"] = result.get("map_data", {})
    
    return response_data

