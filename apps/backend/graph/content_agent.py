"""
LangGraph agent workflow using Vertex AI.
Implements a multi-step conversation agent with guardrails.
"""

from typing import Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from core.vertex_ai import get_vertex_ai_service, VertexAIAgentState
from core.guardrails import get_message_guardrails
from core.chunking import get_chunker
from core.embeddings import get_embedding_service


class AgentState(BaseModel):
    """State for LangGraph agent."""
    
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str
    conversation_id: str
    safety_check_passed: bool = False
    embedding_stored: bool = False


class ContentGenerationAgent:
    """LangGraph agent for content generation with Vertex AI."""
    
    def __init__(
        self,
        gcp_project_id: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        safety_level: str = "moderate",
    ):
        """
        Initialize the content generation agent.
        
        Args:
            gcp_project_id: GCP project ID
            model: Vertex AI model to use
            safety_level: Safety filtering level
        """
        self.vertex_ai = get_vertex_ai_service(
            project_id=gcp_project_id,
            model=model,
            safety_level=safety_level
        )
        self.guardrails = get_message_guardrails(safety_level)
        self.embedder = get_embedding_service()
        self.chunker = get_chunker("medium")
    
    def safety_check_node(self, state: dict) -> dict:
        """
        Validate input message safety.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        
        if not messages:
            return state
        
        # Check last user message
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return state
        
        # Validate with guardrails
        result = self.guardrails.validate_user_message(
            last_message.content,
            role="user"
        )
        
        if not result.is_safe:
            # Add safety error message
            error_msg = AIMessage(
                content=f"⚠️ Message failed safety check: {result.reason}"
            )
            state["messages"] = list(state["messages"]) + [error_msg]
            state["safety_check_passed"] = False
            return state
        
        state["safety_check_passed"] = True
        return state
    
    def llm_node(self, state: dict) -> dict:
        """
        Call Vertex AI LLM for response generation.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with LLM response
        """
        # Skip if safety check failed
        if not state["safety_check_passed"]:
            return state
        
        # Get messages
        messages = state["messages"]
        
        # Add system prompt if not present
        has_system = any(isinstance(m, SystemMessage) for m in messages)
        if not has_system:
            system_msg = SystemMessage(
                content="You are a helpful AI content generation assistant. "
                        "Generate high-quality, engaging content."
            )
            messages = [system_msg] + list(messages)
        
        # Invoke LLM
        response = self.vertex_ai.invoke(messages)
        
        # Add response to messages
        state["messages"] = list(state["messages"]) + [response]
        
        return state
    
    def embedding_node(self, state: dict) -> dict:
        """
        Generate embeddings for the response.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state
        """
        # Skip if no valid response
        if not state["safety_check_passed"]:
            state["embedding_stored"] = False
            return state
        
        messages = state["messages"]
        
        # Find last AI message
        ai_response = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                ai_response = msg
                break
        
        if not ai_response:
            return state
        
        # Generate embeddings (would normally save to DB)
        try:
            chunks = self.chunker.split_text(ai_response.content)
            state["embedding_stored"] = True
        except Exception as e:
            print(f"Embedding error: {e}")
            state["embedding_stored"] = False
        
        return state
    
    def create_graph(self):
        """
        Create LangGraph workflow.
        
        Returns:
            Compiled graph
        """
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("safety_check", self.safety_check_node)
        workflow.add_node("llm", self.llm_node)
        workflow.add_node("embedding", self.embedding_node)
        
        # Add edges
        workflow.set_entry_point("safety_check")
        workflow.add_edge("safety_check", "llm")
        workflow.add_edge("llm", "embedding")
        workflow.add_edge("embedding", END)
        
        # Compile
        return workflow.compile()
    
    def invoke(self, user_message: str, conversation_history: list[BaseMessage] = None) -> str:
        """
        Invoke the agent to generate a response.
        
        Args:
            user_message: User input
            conversation_history: Previous messages
            
        Returns:
            Generated response
        """
        # Build initial state
        messages = conversation_history or []
        messages = list(messages) + [HumanMessage(content=user_message)]
        
        state = {
            "messages": messages,
            "safety_check_passed": False,
            "embedding_stored": False,
        }
        
        # Create and run graph
        graph = self.create_graph()
        result = graph.invoke(state)
        
        # Extract response
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."


def create_agent(
    gcp_project_id: Optional[str] = None,
    model: str = "gemini-2.0-flash",
    safety_level: str = "moderate",
) -> ContentGenerationAgent:
    """
    Create a content generation agent.
    
    Args:
        gcp_project_id: GCP project ID
        model: Vertex AI model
        safety_level: Safety level
        
    Returns:
        ContentGenerationAgent instance
    """
    return ContentGenerationAgent(
        gcp_project_id=gcp_project_id,
        model=model,
        safety_level=safety_level,
    )


# Example usage
if __name__ == "__main__":
    # Create agent
    agent = create_agent(
        gcp_project_id="your-gcp-project",
        model="gemini-2.0-flash",
        safety_level="moderate"
    )
    
    # Test conversation
    user_input = "Write a blog post about AI ethics"
    
    try:
        response = agent.invoke(user_input)
        print(f"User: {user_input}")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure GCP_PROJECT_ID is set and Vertex AI is enabled.")
