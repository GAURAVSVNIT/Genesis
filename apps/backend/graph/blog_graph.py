from langgraph.graph import StateGraph
from agents.intent import extract_intent
from agents.blog_writer import write_blog
from agents.safety import safety_check

class BlogState(dict):
    pass

graph = StateGraph(BlogState)

graph.add_node("intent", extract_intent)
graph.add_node("write", write_blog)
graph.add_node("safety", safety_check)

graph.set_entry_point("intent")
graph.add_edge("intent", "write")
graph.add_edge("write", "safety")

blog_graph = graph.compile()