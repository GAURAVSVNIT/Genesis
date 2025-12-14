from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv
dotenv.load_dotenv()
import os

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=os.getenv("GOOGLE_API_KEY"))

async def extract_intent(state):
    prompt = f"""
    Extract intent from:
    {state['prompt']}
    Return topic and audience.
    """
    res = llm.invoke(prompt)
    state['intent'] = res.content
    return state