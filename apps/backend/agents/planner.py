import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.0-flash")

async def plan(state):
    """
    Planner Agent - Creates detailed execution plan
    Breaks down the task into actionable steps
    """
    coordination = state.get('coordination', '')
    
    prompt = f"""
    You are the Planner Agent. Based on the task: '{state['task']}'
    
    Coordinator's guidance: {coordination}
    
    Your responsibilities:
    1. Break down the task into clear, sequential steps
    2. Organize the approach with clear headings and structure
    3. Identify what information or actions are needed for each step
    
    Create a detailed plan that the Executor can follow.
    Format your plan with numbered steps and clear instructions.
    """
    
    res = await llm.ainvoke(prompt)
    state["plan"] = res.content
    return state
