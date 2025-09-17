from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"]="AIzaSyBsR-2-MAb1WUTrh-qj7g3YE4QxQCgCJGw"

llm=init_chat_model("google_genai:gemini-2.0-flash")

#creating state graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder= StateGraph(State)

#adding a node to stategraph
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

#adding an entry point to tell the graph where to start its work
graph_builder.add_edge(START, "chatbot")

#adding an exit point to indicate where the graph should finish its execution
graph_builder.add_edge("chatbot", END)

#compiling the graph
graph=graph_builder.compile()

#visualizing the graph
def visualize_mermaid():
    """Visualize using Mermaid diagram"""
    try:
        from IPython.display import Image, display
        display(Image(graph.get_graph().draw_mermaid_png()))
        print("✅ Mermaid visualization displayed successfully")
    except ImportError:
        print("❌ IPython not available for Mermaid visualization")
    except Exception as e:
        print(f"❌ Mermaid visualization failed: {e}")
        print("💡 Tip: Try installing graphviz: pip install graphviz")

if __name__=="__main__":
    visualize_mermaid()