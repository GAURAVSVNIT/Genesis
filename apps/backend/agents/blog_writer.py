import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.0-flash")

async def write_blog(state):
    prompt = f"""
    Write a {state['length']} blog.
    Tone: {state['tone']}
    Topic: {state['intent']}

    Structure:
    - Title
    - Introduction
    - Headings
    - Conclusion
    """
    res = await llm.ainvoke(prompt)
    state["blog"] = res.content
    return state