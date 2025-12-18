import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.0-flash")

async def extract_intent(state):
    prompt = f"""
    Extract intent from:
    {state['prompt']}
    Return topic and audience.
    """
    res = await llm.ainvoke(prompt)
    state['intent'] = res.content
    return state