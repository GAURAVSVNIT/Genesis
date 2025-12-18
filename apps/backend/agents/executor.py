import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.0-flash")

async def execute(state):
    """
    Executor Agent - Executes the plan created by Planner
    Generates the actual output/solution
    """
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
