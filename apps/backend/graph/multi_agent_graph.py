from langgraph.graph import StateGraph
from agents.coordinator import coordinate
from agents.planner import plan
from agents.executor import execute
from agents.reviewer import review

from typing import TypedDict, Optional

class MultiAgentState(TypedDict):
    task: str
    coordination: Optional[str]
    plan: Optional[str]
    execution: Optional[str]
    final_output: Optional[str]
    status: Optional[str]

# Create the state graph
graph = StateGraph(MultiAgentState)

# Add agent nodes in sequential order
graph.add_node("coordinator", coordinate)
graph.add_node("planner", plan)
graph.add_node("executor", execute)
graph.add_node("reviewer", review)

# Define sequential flow: coordinator -> planner -> executor -> reviewer
graph.set_entry_point("coordinator")
graph.add_edge("coordinator", "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "reviewer")
graph.set_finish_point("reviewer")

# Compile the graph
multi_agent_graph = graph.compile()
