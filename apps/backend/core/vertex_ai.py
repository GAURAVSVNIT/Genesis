"""
Vertex AI integration with LangChain and LangGraph.
Uses Google Cloud Vertex AI for LLM operations.
"""

import os
from typing import Optional
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from core.guardrails import get_message_guardrails, SafetyLevel
from core.config import settings
import warnings
from langchain_core._api import LangChainDeprecationWarning

# Suppress LangChain deprecation warning for ChatVertexAI
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


class VertexAIConfig:
    """Configuration for Vertex AI."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ):
        """
        Initialize Vertex AI config.
        
        Args:
            project_id: GCP project ID (from environment if not provided)
            location: GCP region
            model: Model name (e.g., "gemini-2.0-flash", "gemini-1.5-pro")
            temperature: Model temperature (0-2)
            max_output_tokens: Max tokens in response
        """
        self.project_id = project_id or settings.GCP_PROJECT_ID or os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID not found. Set it in .env file, settings, or pass as parameter.")


class VertexAIService:
    """Service for interacting with Vertex AI LLM."""
    
    def __init__(
        self,
        config: Optional[VertexAIConfig] = None,
        safety_level: str = "permissive",  # Changed from 'moderate' for development
    ):
        """
        Initialize Vertex AI service.
        
        Args:
            config: VertexAIConfig instance
            safety_level: 'strict', 'moderate', 'permissive'
        """
        self.config = config or VertexAIConfig()
        self.guardrails = get_message_guardrails(safety_level)
        
        # Initialize Vertex AI LLM
        self.llm = ChatVertexAI(
            model_name=self.config.model,
            project=self.config.project_id,
            location=self.config.location,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
        )
    
    def validate_input(self, text: str) -> bool:
        """
        Validate input message with guardrails.
        
        Args:
            text: Message to validate
            
        Returns:
            True if safe, False otherwise
        """
        result = self.guardrails.validate_user_message(text, role="user")
        return result.is_safe
    
    def get_input_safety_report(self, text: str) -> dict:
        """
        Get detailed safety report for input.
        
        Args:
            text: Message to analyze
            
        Returns:
            Safety report
        """
        return self.guardrails.get_safety_report(text)
    
    async def ainvoke(self, messages: list[BaseMessage] | str) -> AIMessage:
        """
        Async invoke Vertex AI LLM.
        
        Args:
            messages: List of messages or prompt string
            
        Returns:
            AIMessage response
        """
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
            
        # Validate user messages
        for msg in messages:
            if isinstance(msg, HumanMessage):
                if not self.validate_input(msg.content):
                    raise ValueError(f"Message failed safety checks: {msg.content[:50]}")
        
        # Call LLM
        response = await self.llm.ainvoke(messages)
        return response

    def invoke(self, messages: list[BaseMessage] | str) -> AIMessage:
        """
        Invoke Vertex AI LLM.
        
        Args:
            messages: List of messages or prompt string
            
        Returns:
            AIMessage response
        """
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]

        # Validate user messages
        for msg in messages:
            if isinstance(msg, HumanMessage):
                if not self.validate_input(msg.content):
                    raise ValueError(f"Message failed safety checks: {msg.content[:50]}")
        
        # Call LLM
        response = self.llm.invoke(messages)
        return response
    
    def stream(self, messages: list[BaseMessage]):
        """
        Stream response from Vertex AI LLM.
        
        Args:
            messages: List of messages
            
        Yields:
            Response chunks
        """
        for chunk in self.llm.stream(messages):
            yield chunk
    
    def batch(self, messages_list: list[list[BaseMessage]]) -> list[AIMessage]:
        """
        Batch invoke Vertex AI LLM.
        
        Args:
            messages_list: List of message lists
            
        Returns:
            List of responses
        """
        responses = []
        for messages in messages_list:
            response = self.invoke(messages)
            responses.append(response)
        return responses


class VertexAIAgentState:
    """State management for LangGraph agent."""
    
    def __init__(self):
        """Initialize agent state."""
        self.messages: list[BaseMessage] = []
        self.current_input: str = ""
        self.safety_report: dict = {}
        self.is_safe: bool = False
    
    def add_message(self, role: str, content: str):
        """
        Add message to state.
        
        Args:
            role: 'user', 'assistant', 'system'
            content: Message content
        """
        if role == "user":
            self.messages.append(HumanMessage(content=content))
        elif role == "assistant":
            self.messages.append(AIMessage(content=content))
        elif role == "system":
            self.messages.append(SystemMessage(content=content))
    
    def get_messages(self) -> list[BaseMessage]:
        """Get all messages."""
        return self.messages
    
    def clear(self):
        """Clear all messages."""
        self.messages = []


def create_vertex_ai_service(
    project_id: Optional[str] = None,
    model: str = "gemini-2.0-flash",
    safety_level: str = "permissive"  # Changed from 'moderate' for development
) -> VertexAIService:
    """
    Create a Vertex AI service instance.
    
    Args:
        project_id: GCP project ID
        model: Model name
        safety_level: Safety filtering level
        
    Returns:
        VertexAIService instance
    """
    config = VertexAIConfig(
        project_id=project_id,
        model=model
    )
    return VertexAIService(config=config, safety_level=safety_level)


# Singleton instance
_vertex_ai_service: Optional[VertexAIService] = None


def get_vertex_ai_service(
    project_id: Optional[str] = None,
    model: str = "gemini-2.0-flash",
    safety_level: str = "permissive"  # Changed from 'moderate' for development
) -> VertexAIService:
    """Get or create Vertex AI service instance."""
    global _vertex_ai_service
    if _vertex_ai_service is None:
        _vertex_ai_service = create_vertex_ai_service(
            project_id=project_id,
            model=model,
            safety_level=safety_level
        )
    return _vertex_ai_service


# Example usage
if __name__ == "__main__":
    # Initialize service
    service = get_vertex_ai_service(
        project_id="your-gcp-project",
        model="gemini-2.0-flash"
    )
    
    # Test message
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content="What is machine learning?")
    ]
    
    # Check safety
    for msg in messages:
        if isinstance(msg, HumanMessage):
            report = service.get_input_safety_report(msg.content)
            print(f"Safety: {report['overall']['is_safe']}")
    
    # Invoke LLM
    response = service.invoke(messages)
    print(f"Response: {response.content}")
