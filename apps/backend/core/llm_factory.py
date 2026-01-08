from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from core.config import settings

class LLMFactory:
    """Factory for creating LLM instances based on provider/model."""
    
    @staticmethod
    def get_llm(model_name: str = "gemini-2.0-flash", temperature: float = 0.7) -> BaseChatModel:
        """
        Get an LLM instance.
        
        Supported models:
        - gemini-* (Google Vertex AI)
        - gpt-* (OpenAI)
        - llama3-*, mixtral-* (Groq)
        """
        
        # Google / Vertex AI
        if model_name.startswith("gemini"):
            from langchain_google_vertexai import ChatVertexAI
            # Map simplified names if needed, or pass directly
            return ChatVertexAI(
                model_name=model_name,
                temperature=temperature,
                project=settings.GCP_PROJECT_ID,
                convert_system_message_to_human=True # specific fix for some gemini versions
            )
            
        # OpenAI
        elif model_name.startswith("gpt"):
            print(f" [LLMFactory] Initializing OpenAI Chat Model: {model_name}")
            from langchain_openai import ChatOpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment")
                
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY
            )
            
        # Groq (Open Source Models)
        elif "llama" in model_name or "mixtral" in model_name or "groq" in model_name:
            from langchain_groq import ChatGroq
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not found in environment")
                
            # Groq model mapping if specific names are passed
            # e.g. "llama3-70b" -> "llama-3.3-70b-versatile"
            real_model = model_name
            if model_name in ["llama3-70b", "llama3-70b-8192"]:
                real_model = "llama-3.3-70b-versatile"
            elif model_name in ["llama3-8b", "llama3-8b-8192"]:
                real_model = "llama-3.1-8b-instant"
            elif model_name == "mixtral-8x7b":
                real_model = "mixtral-8x7b-32768"
                
            return ChatGroq(
                model_name=real_model,
                temperature=temperature,
                api_key=settings.GROQ_API_KEY
            )
            
        else:
            # Default fallback
            print(f"⚠️ Unknown model '{model_name}', falling back to Gemini")
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model_name="gemini-2.0-flash",
                temperature=temperature,
                project=settings.GCP_PROJECT_ID
            )
