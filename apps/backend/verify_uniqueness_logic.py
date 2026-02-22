
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vertex_ai_embeddings import get_vertex_ai_embedding_service
from database.database import SessionLocal
from database.models.content import GeneratedContent, ContentEmbedding
from sqlalchemy import func, text
import uuid

async def verify_uniqueness():
    print("Verifying Uniqueness Logic...")
    
    # Initialize service
    service = get_vertex_ai_embedding_service()
    
    # Test content
    content1 = "The quick brown fox jumps over the lazy dog."
    content2 = "A fast brown fox leaps over a sleepy dog." # Similar
    content3 = "Quantum mechanics describes the behavior of matter at atomic scales." # Different
    
    print(f"Content 1: {content1}")
    print(f"Content 2: {content2}")
    print(f"Content 3: {content3}")

    # Generate embeddings
    print("Generating embeddings...")
    embedding1 = service.generate_embedding(content1)
    embedding2 = service.generate_embedding(content2)
    embedding3 = service.generate_embedding(content3)
    
    # Simulate DB check
    db = SessionLocal()
    try:
        # Create a temporary embedding for Content 1 to query against
        # In a real scenario, this would be in the DB. 
        # For this test, we'll manually calculate cosine distance using pgvector syntax logic if possible, 
        # or just insert it and query. Inserting is safer to test the DB operator.
        
        # Cleanup previous test data
        db.execute(text("DELETE FROM content_embeddings WHERE content_id IN (SELECT id FROM generated_content WHERE original_prompt LIKE 'TEST_UNIQUENESS%')"))
        db.execute(text("DELETE FROM generated_content WHERE original_prompt LIKE 'TEST_UNIQUENESS%'"))
        db.commit()
        
        print("Inserting Content 1...")
        cid1 = str(uuid.uuid4())
        try:
            gc1 = GeneratedContent(
                id=cid1, 
                original_prompt="TEST_UNIQUENESS_1", 
                content_type="text", 
                user_id=None,
                generated_content={"text": "dummy content"},
                requirements={},
                platform="test",
                status="draft"
            )
            db.add(gc1)
            db.commit()
            print("Content 1 inserted successfully.")
        except Exception as e:
            print(f"Failed to insert Content 1: {e}")
            import traceback
            traceback.print_exc()
            return
        
        service.store_embedding(cid1, content1, db)
        print("Inserted Content 1 and its embedding.")
        
        from pgvector.sqlalchemy import Vector
        
        # Check Content 2 uniqueness
        print("Checking Content 2 uniqueness against DB...")
        query_embedding = embedding2
        
        # Test existing find_similar_content method
        print("Testing service.find_similar_content with Content 2...")
        similar = service.find_similar_content(content2, limit=1, db=db)
        print(f"Found {len(similar)} similar items.")
        if similar:
            print(f"Top match ID: {similar[0].id}")
            print(f"Top match Prompt: {similar[0].original_prompt}")
        else:
            print("No matches found via find_similar_content.")


            
    finally:
        # Cleanup
        db.execute(text("DELETE FROM content_embeddings WHERE content_id IN (SELECT id FROM generated_content WHERE original_prompt LIKE 'TEST_UNIQUENESS%')"))
        db.execute(text("DELETE FROM generated_content WHERE original_prompt LIKE 'TEST_UNIQUENESS%'"))
        db.commit()
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_uniqueness())
