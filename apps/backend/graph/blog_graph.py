from langgraph.graph import StateGraph
from agents.intent import extract_intent
from agents.blog_writer import write_blog
from agents.safety import safety_check

from typing import TypedDict, Optional

class BlogState(TypedDict):
    prompt: str
    tone: str
    length: str
    intent: Optional[str]
    blog: Optional[str]
    status: Optional[str]

graph = StateGraph(BlogState)

graph.add_node("intent_agent", extract_intent)
graph.add_node("write_agent", write_blog)
graph.add_node("safety_agent", safety_check)

graph.set_entry_point("intent_agent")
graph.add_edge("intent_agent", "write_agent")
graph.add_edge("write_agent", "safety_agent")
graph.set_finish_point("safety_agent")

blog_graph = graph.compile()