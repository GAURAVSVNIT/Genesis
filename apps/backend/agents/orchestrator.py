from schemas import BlogRequest
import os
from dotenv import load_dotenv
from core.vertex_ai import get_vertex_ai_service

load_dotenv()

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize Vertex AI service
llm = get_vertex_ai_service(
    project_id=os.getenv("GCP_PROJECT_ID"),
    model="gemini-2.5-flash"
)

async def run_blog_agent(req: BlogRequest):
    prompt = f"""Write a {req.length} blog post with a {req.tone} tone about: {req.prompt}

Structure:
- Title
- Introduction
- 2-3 main sections with headings
- Conclusion

Make it engaging and well-formatted."""
    
    result = await llm.ainvoke(prompt)
    return {"blog": result.content}