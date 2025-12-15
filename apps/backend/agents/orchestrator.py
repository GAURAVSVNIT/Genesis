from schemas import BlogRequest
import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash", 
    api_key=os.getenv("GOOGLE_API_KEY")
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