import os
import dotenv
from core.config import settings

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

async def review(state):
    """
    Reviewer Agent - Quality assurance and final review
    Validates the execution and provides the final polished output
    """
    # Initialize Vertex AI service lazily
    project_id = os.getenv("GCP_PROJECT_ID") or settings.GCP_PROJECT_ID
    llm = get_vertex_ai_service(project_id=project_id, model="gemini-2.5-flash")
    execution = state.get('execution', '')
    
    prompt = f"""
    You are the Reviewer Agent. Review and refine this output:
    
    {execution}
    
    Original task: '{state['task']}'
    
    Your responsibilities:
    1. Review the output for quality, accuracy, and completeness
    2. Make necessary improvements and corrections
    3. Ensure the output fully addresses the original task
    4. Polish the final output for clarity and professionalism
    
    Provide the final, polished version of the output.
    If the execution is already excellent, you may keep it as is but confirm its quality.
    """
    
    res = await llm.ainvoke(prompt)
    state["final_output"] = res.content
    state["status"] = "completed"
    return state
