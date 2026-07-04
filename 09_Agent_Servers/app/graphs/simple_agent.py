from __future__ import annotations

from app.tools import get_tool_belt
from app.state import MessagesState
from app.models import get_chat_model, fix_tool_calls
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = (
    "You are a helpful assistant specialized in feline (cat) health. "
    "Use the retrieve_information tool for cat-health questions, web search for "
    "current information, and Arxiv for research papers. Cite tool results when "
    "they inform your answer."
)

## original graph
#graph = create_agent(
#    model=get_chat_model(),
#    tools=get_tool_belt(),
#    system_prompt=SYSTEM_PROMPT,
#)

def _build_model_with_tools():
     """Return a chat model instance bound to the current tool belt."""
     model = get_chat_model()
     return model.bind_tools(get_tool_belt())

def call_model(state: MessagesState) -> dict:
    """Invoke the model with the accumulated messages and append its response."""
    model = _build_model_with_tools()
    messages = state["messages"]
    response = fix_tool_calls(model.invoke(messages))
    return {"messages": [response]}

def build_graph():
    """Build an agent graph that interleaves model and tool execution."""
    graph = StateGraph(MessagesState)
    tool_node = ToolNode(get_tool_belt())
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "action", END: END})
    graph.add_edge("action", "agent")
    return graph

# compile the graph
graph = build_graph().compile()




