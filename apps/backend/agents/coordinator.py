import os
import dotenv
from core.config import settings

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

async def coordinate(state):
    """
    Coordinator Agent - Oversees the entire workflow
    Analyzes the user request and provides guidance to other agents
    """
    # Initialize Vertex AI service lazily
    project_id = os.getenv("GCP_PROJECT_ID") or settings.GCP_PROJECT_ID
    llm = get_vertex_ai_service(project_id=project_id, model="gemini-2.5-flash")
    prompt = f"""
    You are the Coordinator Agent overseeing this task: '{state['task']}'
    
    Your responsibilities:
    1. Understand the user's intent and requirements
    2. Provide high-level guidance for the workflow
    3. Identify key objectives and success criteria
    
    Analyze the task and provide clear guidance for the planning phase.
    Be concise and focus on what needs to be achieved.
    """
    
    res = await llm.ainvoke(prompt)
    state["coordination"] = res.content
    return state
