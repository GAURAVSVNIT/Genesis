import os
import sys

# Add current directory to path so we can import core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_factory import LLMFactory
from core.config import settings
from langchain_core.messages import HumanMessage

def test_openai():
    print("Testing OpenAI Integration...")
    
    # Check Key
    key = settings.OPENAI_API_KEY
    if not key:
        print("❌ CRITICAL: OPENAI_API_KEY is missing from settings/env!")
        return
    
    masked_key = key[:5] + "..." + key[-4:]
    print(f"✅ Found API Key: {masked_key}")
    
    # Instantiate
    try:
        print("Instantiating ChatOpenAI via LLMFactory...")
        llm = LLMFactory.get_llm("gpt-4o")
        print(f"✅ Model Created: {type(llm)}")
    except Exception as e:
        print(f"❌ Failed to instantiate: {e}")
        return

    # Invoke
    try:
        print("Sending request to OpenAI (gpt-4o)...")
        messages = [HumanMessage(content="Hello, are you GPT-4o? Reply with 'YES, I AM GPT-4o' if you are.")]
        response = llm.invoke(messages)
        print("✅ Response Received!")
        print("-" * 20)
        print(response.content)
        print("-" * 20)
        
        if hasattr(response, 'response_metadata'):
             print(f"Metadata: {response.response_metadata}")
             
    except Exception as e:
         print(f"❌ Failed to invoke: {e}")

if __name__ == "__main__":
    test_openai()
