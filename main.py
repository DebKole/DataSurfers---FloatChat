from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class AgentState(TypedDict):
    querys: List[HumanMessage]
    answers: List[AIMessage]

def add_query(query: str) -> AgentState:
    state: AgentState = {"querys": [], "answers": []}
    state["querys"].append(HumanMessage(content=query))
    return state

def node(state: AgentState) -> AgentState:
    history = []
    for q, a in zip(state["querys"], state["answers"]):
        history.append(q)   # keep as HumanMessage
        history.append(a)   # keep as AIMessage
    last_query = state["querys"][-1]
    history.append(last_query)

    response = llm.invoke(history)  # returns AIMessage
    state["answers"].append(response)
    return state

graph = StateGraph(AgentState)
graph.add_node("ai", node)
graph.add_edge(START, "ai")
graph.add_edge("ai", END)

model = graph.compile()

input_state = add_query("what is ARGO?")
result = model.invoke(input_state)

print(result["answers"][-1].content)
