import os
from core.config import settings

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

async def execute(state):
    """
    Executor Agent - Executes the plan created by Planner
    Generates the actual output/solution
    """
    # Initialize Vertex AI service lazily
    project_id = os.getenv("GCP_PROJECT_ID") or settings.GCP_PROJECT_ID
    llm = get_vertex_ai_service(project_id=project_id, model="gemini-2.0-flash")
    plan = state.get('plan', '')
    
    prompt = f"""
    You are the Executor Agent. Your task is to execute this plan:
    
    {plan}
    
    Original task: '{state['task']}'
    
    Your responsibilities:
    1. Follow the plan step-by-step
    2. Generate comprehensive, detailed output
    3. Include all necessary information and context
    4. Ensure the solution directly addresses the original task
    
    Execute the plan thoroughly and produce the final output.
    Be comprehensive and detailed in your execution.
    """
    
    res = await llm.ainvoke(prompt)
    state["execution"] = res.content
    return state
