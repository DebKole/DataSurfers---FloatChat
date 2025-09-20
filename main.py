from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
import os
from data_processor import ArgoDataProcessor
from query_interpreter import QueryInterpreter

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

# Initialize data processor and query interpreter
data_processor = ArgoDataProcessor("argo_demo.csv")
query_interpreter = QueryInterpreter(data_processor)

class AgentState(TypedDict):
    querys: List[HumanMessage]
    answers: List[AIMessage]
    use_data: bool
    data_response: dict
    show_map: bool
    map_data: dict

def add_query(query: str) -> AgentState:
    state: AgentState = {"querys": [], "answers": [], "use_data": False, "data_response": {}, "show_map": False, "map_data": {}}
    state["querys"].append(HumanMessage(content=query))
    return state

def data_query_node(state: AgentState) -> AgentState:
    """Node that processes queries using local Argo data."""
    last_query = state["querys"][-1].content
    
    # Check if query is about oceanographic data
    data_keywords = ['temperature', 'temp', 'salinity', 'sal', 'depth', 'surface', 'profile', 
                    'thermocline', 'ocean', 'water', 'argo', 'float', 'pressure', 'statistics',
                    'summary', 'conditions', 'compare', 'analysis', 'gradient']
    
    query_lower = last_query.lower()
    is_data_query = any(keyword in query_lower for keyword in data_keywords)
    
    if is_data_query:
        # Use local data to answer the query
        result = query_interpreter.interpret_query(last_query)
        state["use_data"] = True
        state["data_response"] = result
        
        # Create AI message with the data-driven response
        ai_response = AIMessage(content=result['response'])
        state["answers"].append(ai_response)
        
        # Check if this should show a map
        if result.get('show_map', False):
            state["show_map"] = True
            state["map_data"] = {
                'map_data': result.get('map_data', []),
                'parameter': result.get('map_parameter', 'temperature'),
                'region': result.get('map_region'),
                'query_type': result.get('query_type', 'map_visualization')
            }
    else:
        # Fall back to LLM for general queries
        state["use_data"] = False
    
    return state

def llm_node(state: AgentState) -> AgentState:
    """Node that uses LLM for general queries."""
    if not state["use_data"]:  # Only use LLM if data node didn't handle it
        history = []
        for q, a in zip(state["querys"], state["answers"]):
            history.append(q)
            history.append(a)
        
        last_query = state["querys"][-1]
        history.append(last_query)
        
        # Add context about available data
        context_message = HumanMessage(content="""You are FloatChat, an oceanographic data assistant. 
        You have access to Argo float data with temperature, salinity, pressure measurements at various depths.
        If users ask about specific oceanographic data, guide them to ask more specific questions about 
        temperature, salinity, depth profiles, or surface conditions.""")
        
        history.insert(0, context_message)
        
        response = llm.invoke(history)
        state["answers"].append(response)
    
    return state

def route_query(state: AgentState) -> str:
    """Route to appropriate node based on query type."""
    return "llm" if not state["use_data"] else END

# Create the graph
graph = StateGraph(AgentState)
graph.add_node("data_query", data_query_node)
graph.add_node("llm", llm_node)

# Add edges
graph.add_edge(START, "data_query")
graph.add_conditional_edges("data_query", route_query, {"llm": "llm", END: END})
graph.add_edge("llm", END)

model = graph.compile()