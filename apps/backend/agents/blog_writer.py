import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=os.getenv("GOOGLE_API_KEY"))

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