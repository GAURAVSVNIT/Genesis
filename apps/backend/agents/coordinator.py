import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.0-flash")

async def coordinate(state):
    """
    Coordinator Agent - Oversees the entire workflow
    Analyzes the user request and provides guidance to other agents
    """
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
