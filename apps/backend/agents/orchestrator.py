from schemas import BlogRequest
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get API key with fallback
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=api_key
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