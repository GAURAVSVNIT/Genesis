import asyncio
import os
import sys
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Add backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from graph.blog_graph import blog_graph

async def test_blog_generation():
    print(" Starting Blog Workflow Test...")
    
    # Initial state
    initial_state = {
        "prompt": "The future of AI in software development",
        "tone": "professional",
        "length": "short", # Keep it short for faster testing
        "keywords": [],
        "iteration_count": 0
    }
    
    print(f" Initial State: {initial_state}")
    
    # Run the graph
    try:
        # Use ainvoke to run the graph
        result = await blog_graph.ainvoke(initial_state)
        
        print("\n Workflow Completed Successfully!")
        print("-" * 50)
        
        # Check Trend Data
        print(f" Trend Context: {result.get('trend_context')[:100]}...")
        
        # Check Blog Content
        print(f" Blog Length: {len(result.get('blog', ''))} chars")
        
        # Check Uniqueness
        print(f" Is Unique: {result.get('is_unique')}")
        print(f" Similarity Score: {result.get('similarity_score')}")
        
        # Check SEO
        print(f" SEO Score: {result.get('seo_score')}")
        print(f" Iterations: {result.get('iteration_count')}")
        
    except Exception as e:
        print(f"\n Workflow Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_blog_generation())
