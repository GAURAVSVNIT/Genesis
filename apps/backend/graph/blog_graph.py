from langgraph.graph import StateGraph, END
from agents.intent import extract_intent
from agents.blog_writer import write_blog
from agents.safety import safety_check

# Import new agents
from graph.trend_agent import analyze_trends
from graph.uniqueness_agent import check_uniqueness
from graph.seo_agent import evaluate_seo
from graph.image_agent import generate_image

from typing import TypedDict, Optional, List, Dict, Any

class BlogState(TypedDict):
    prompt: str
    tone: str
    length: str
    intent: Optional[str]
    blog: Optional[str]
    status: Optional[str]
    image_url: Optional[str] # Added image_url field
    
    # Trend Analysis Fields
    keywords: List[str]
    trend_data: Dict[str, Any]
    trend_context: str
    
    # Uniqueness Fields
    is_unique: bool
    similarity_score: float
    uniqueness_feedback: str
    
    # SEO Fields
    seo_result: Dict[str, Any]
    seo_score: float
    seo_status: str
    seo_feedback: str
    iteration_count: int

# Define the graph
graph = StateGraph(BlogState)

# Add Nodes
graph.add_node("initial_safety_agent", safety_check)
graph.add_node("intent_agent", extract_intent)
graph.add_node("trend_agent", analyze_trends)
graph.add_node("write_agent", write_blog)
graph.add_node("uniqueness_agent", check_uniqueness)
graph.add_node("seo_agent", evaluate_seo)
graph.add_node("image_agent", generate_image)
graph.add_node("safety_agent", safety_check)

# Set Entry Point
graph.set_entry_point("initial_safety_agent")

# Define Edges

# 0. Initial Safety -> Intent (or End)
def route_initial_safety(state: BlogState):
    if state.get("status") == "unsafe":
        return END
    return "intent_agent"

graph.add_conditional_edges(
    "initial_safety_agent",
    route_initial_safety,
    {
        "intent_agent": "intent_agent",
        END: END
    }
)

# 1. Intent -> Trend
graph.add_edge("intent_agent", "trend_agent")

# 2. Trend -> Write
graph.add_edge("trend_agent", "write_agent")

# 3. Write -> Uniqueness
graph.add_edge("write_agent", "uniqueness_agent")

# 4. Conditional Edge from Uniqueness Agent
def route_after_uniqueness(state: BlogState):
    # If not unique, go back to write (regenerate)
    if not state.get("is_unique", True):
        return "write_agent"
    return "seo_agent"

graph.add_conditional_edges(
    "uniqueness_agent",
    route_after_uniqueness,
    {
        "write_agent": "write_agent",
        "seo_agent": "seo_agent"
    }
)

# 5. Conditional Edge from SEO Agent
def route_after_seo(state: BlogState):
    status = state.get("seo_status", "accept")
    
    if status == "revise":
        return "write_agent"
    return "image_agent" # Proceed to Image Generation

graph.add_conditional_edges(
    "seo_agent",
    route_after_seo,
    {
        "write_agent": "write_agent",
        "image_agent": "image_agent"
    }
)

# 6. Image -> Safety
graph.add_edge("image_agent", "safety_agent")

# 7. Safety -> End
graph.set_finish_point("safety_agent")

blog_graph = graph.compile()