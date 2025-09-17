from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"]="AIzaSyBsR-2-MAb1WUTrh-qj7g3YE4QxQCgCJGw"

llm=init_chat_model("google_genai:gemini-2.0-flash-lite")

#creating state graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder= StateGraph(State)

#adding a node to stategraph
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"], max_output_tokens=50)]}

graph_builder.add_node("chatbot", chatbot)

#adding an entry point to tell the graph where to start its work
graph_builder.add_edge(START, "chatbot")

#adding an exit point to indicate where the graph should finish its execution
graph_builder.add_edge("chatbot", END)

#compiling the graph
graph=graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages":[{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("goodbye")
            break
        stream_graph_updates(user_input)
    except:
        user_input = "What do you know about LangGraph?"
        print("User: " +user_input)
        stream_graph_updates(user_input)
        break