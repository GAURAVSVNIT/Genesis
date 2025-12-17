import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=os.getenv("GOOGLE_API_KEY"))

async def review(state):
    """
    Reviewer Agent - Quality assurance and final review
    Validates the execution and provides the final polished output
    """
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
