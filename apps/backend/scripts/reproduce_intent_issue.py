
import sys
import os
import asyncio
import json
import requests

# Add backend to path (not strictly needed for requests but good for local ref if we were importing modules)
sys.path.append(os.path.join(os.getcwd(), 'apps', 'backend'))

BACKEND_URL = "http://localhost:8000"

def log_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_classification(prompt):
    log_section(f"Testing Classification for: '{prompt}'")
    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/classify/intent",
            json={"prompt": prompt, "context_summary": ""}
        )
        if response.status_code == 200:
            result = response.json()
            print(f" Intent: {result.get('intent')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Reasoning: {result.get('reasoning')}")
            return result
        else:
            print(f" Custom Error: {response.text}")
            return None
    except Exception as e:
        print(f" Request Error: {e}")
        return None

def test_generation(prompt, intent):
    log_section(f"Testing Generation for: '{prompt}' (Intent: {intent})")
    try:
        payload = {
            "prompt": prompt,
            "intent": intent,
            "conversation_history": [],  # Simulate new chat
            "safety_level": "moderate",
            "model": "gemini-2.0-flash" 
        }
        
        # Increase timeout because generation takes time
        response = requests.post(
            f"{BACKEND_URL}/v1/content/generate",
            json=payload,
            timeout=60 
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', '')
            print(f" Success: {result.get('success')}")
            print(f"   Model Used: {result.get('model')}")
            print(f"\n--- Generated Content Preview ---\n")
            print(content[:500] + "..." if len(content) > 500 else content)
            print("\n-------------------------------\n")
            
            # Check for hallucination or topic shift
            if "crab" in content.lower():
                print(" 'Crab' found in content.")
            else:
                print(" 'Crab' NOT found in content. Possible topic shift.")
                
            if "writing assistant" in content.lower():
                print(" 'Writing Assistant' found in content (User reported issue).")
                
        else:
            print(f" Generation Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f" Generation Request Error: {e}")

if __name__ == "__main__":
    prompt = "Write a blog on Crab"
    
    # 1. Test Classification
    classification = test_classification(prompt)
    
    # 2. If classification works, Test Generation
    if classification:
        # Use the detected intent
        intent = classification.get('intent', 'blog')
        test_generation(prompt, intent)
