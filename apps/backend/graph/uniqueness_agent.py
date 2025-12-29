from typing import Dict, Any, List
from core.embeddings import get_embedding_service
from database.database import SessionLocal
from core.rag_service import RAGService
import numpy as np

def check_uniqueness(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the generated blog content is unique compared to existing content.
    Returns uniqueness status and similarity score.
    """
    blog_content = state.get("blog", "")
    if not blog_content:
        return {"is_unique": True, "similarity_score": 0.0}

    # Use a fresh DB session for this check
    db = SessionLocal()
    try:
        # We need a user_id, assuming it's in state or using a default for now if not passed
        # In a real app, user_id should be in state
        user_id = state.get("user_id", "guest")
        
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Generate embedding for the current draft
        # Note: RAGService.retrieve_similar_content calculates embedding internally for the query
        # We can just use the content as the query to find similar items
        
        similar_items = RAGService.retrieve_similar_content(
            db=db,
            query=blog_content[:1000], # Truncate to 1000 chars for embedding limit
            user_id=user_id,
            limit=1,
            similarity_threshold=0.85
        )
        
        if similar_items:
            # Found similar content
            top_match, score = similar_items[0]
            print(f"DEBUG: Found similar content with score {score}")
            return {
                "is_unique": False, 
                "similarity_score": score,
                "uniqueness_feedback": f"Content is too similar ({score:.2f}) to existing content. Please rewrite to be more unique and differentiate from existing posts."
            }
        
        return {
            "is_unique": True, 
            "similarity_score": 0.0,
            "uniqueness_feedback": ""
        }
        
    except Exception as e:
        print(f"Error in uniqueness check: {e}")
        # Default to unique if check fails to avoid blocking
        return {"is_unique": True, "similarity_score": 0.0}
    finally:
        db.close()
