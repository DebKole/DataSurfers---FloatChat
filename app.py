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
    return {"message":"server is running"}

@app.post("/")
async def query_answer(req:QueryRequest):
    state=add_query(req.query)
    result=model.invoke(state)
    ans=result["answers"][-1].content
    return {"status":201,"message":ans}

