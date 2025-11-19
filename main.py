from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
import os
from mcp_query_agent import MCPQueryAgent

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

# Initialize MCP Query Agent (replaces old data processor)
mcp_agent = MCPQueryAgent()

class AgentState(TypedDict):
    querys: List[HumanMessage]
    answers: List[AIMessage]
    use_data: bool
    data_response: dict
    show_map: bool
    map_data: dict
    table_data: dict

def add_query(query: str) -> AgentState:
    state: AgentState = {"querys": [], "answers": [], "use_data": False, "data_response": {}, "show_map": False, "map_data": {}, "table_data": {}}
    state["querys"].append(HumanMessage(content=query))
    return state

def data_query_node(state: AgentState) -> AgentState:
    """Node that processes queries using MCP tools (Gemini AI + Redis + PostgreSQL)."""
    last_query = state["querys"][-1].content
    
    # Check if query is about oceanographic data
    is_data_query = mcp_agent.is_data_query(last_query)
    
    if is_data_query:
        # Use MCP tools to answer the query
        print(f"🔍 Processing data query via MCP: '{last_query}'")
        result = mcp_agent.execute_query(last_query)
        
        if result['status'] == 'success':
            state["use_data"] = True
            state["data_response"] = result
            
            # Create AI message with the MCP response
            ai_response = AIMessage(content=result['response'])
            state["answers"].append(ai_response)
            
            # Add table data for frontend display
            if result.get('table_data'):
                state["table_data"] = result.get('table_data', {})
            
            # Check if this should show a map
            if result.get('show_map', False):
                state["show_map"] = True
                state["map_data"] = result.get('map_data', {})
        else:
            # MCP query failed, fall back to LLM
            print(f"⚠️ MCP query failed: {result.get('response', 'Unknown error')}")
            state["use_data"] = False
    else:
        # Not a data query, fall back to LLM for general queries
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
        context_message = HumanMessage(content="""You are FloatChat, an oceanographic data assistant with access to Argo float data.

ABOUT ARGO FLOATS:
Argo floats are autonomous oceanographic instruments that drift with ocean currents, diving to depths of up to 2000 meters and surfacing every 10 days to transmit data via satellite. They measure temperature, salinity, and pressure throughout the water column.

YOUR CAPABILITIES:
- Access to thousands of Argo float profiles from the Indian Ocean region
- Temperature, salinity, and pressure measurements at various depths
- Data from regions including Arabian Sea, Bay of Bengal, and Southern Indian Ocean
- Historical data from January 2025 and live/recent data

WHEN USERS ASK INFORMATIONAL QUESTIONS:
- Provide concise, helpful answers (2-3 sentences)
- Explain what Argo floats are and how they work
- Describe available data and capabilities
- Guide them on what specific data queries they can make

EXAMPLE QUERIES:
- "Show me temperature in the Arabian Sea"
- "Get data from float 1902482"
- "What are the salinity patterns in Bay of Bengal?"

IMPORTANT: 
- Keep responses CONCISE (2-4 sentences maximum for informational questions)
- Use plain text only - NO markdown formatting like **bold**, *italic*, or # headers
- Be direct and helpful without being verbose""") 
        
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