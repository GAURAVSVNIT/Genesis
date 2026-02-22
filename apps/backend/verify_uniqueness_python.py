
import asyncio
import os
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models.content import ContentEmbedding, GeneratedContent
from uuid import uuid4

def verify_python_uniqueness():
    print("Verifying Python-side Uniqueness Logic...")
    
    # 1. Fetch recent embeddings (Simulating DB retrieval)
    db = SessionLocal()
    try:
        # Fetch last 50 embeddings
        recent_embeddings = (
            db.query(ContentEmbedding.embedding)
            .order_by(ContentEmbedding.created_at.desc())
            .limit(50)
            .all()
        )
        
        # Extract lists
        # content_embedding.embedding is a list[float] thanks to JSONEncodedList
        vectors = [re.embedding for re in recent_embeddings if re.embedding]
        
        print(f"Fetched {len(vectors)} recent vectors from DB.")
        
        if not vectors:
            print("No vectors in DB. Uniqueness should be 1.0")
            return

        # 2. Simulate new embedding (random for test, or user input)
        # Using the first vector from DB as "new" to test exact match
        new_vector = vectors[0]
        
        # 3. Calculate Similarity
        # Convert to numpy array
        vec_matrix = np.array(vectors)
        new_vec = np.array(new_vector).reshape(1, -1)
        
        print(f"Matrix shape: {vec_matrix.shape}")
        print(f"New vector shape: {new_vec.shape}")
        
        # Calculate cosine similarity
        similarities = cosine_similarity(new_vec, vec_matrix)
        
        # similarities is [[sim1, sim2, ...]]
        max_similarity = np.max(similarities)
        
        print(f"Max Similarity: {max_similarity}")
        
        uniqueness_score = 1.0 - max_similarity
        print(f"Uniqueness Score: {uniqueness_score}")
        
        # Verify result
        # Since new_vector is identical to vectors[0], max_similarity should be ~1.0
        # Uniqueness should be ~0.0
        
        if max_similarity > 0.99:
            print("SUCCESS: Detected identical content correctly.")
        else:
            print("FAILURE: Did not detect identical content.")
            
        # Test distinct content
        # Create an orthogonal vector (or random)
        random_vec = np.random.rand(1, len(new_vector)).flatten()
        
        should_be_unique = 1.0 - np.max(cosine_similarity(random_vec.reshape(1, -1), vec_matrix))
        print(f"Random Vector Uniqueness: {should_be_unique}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_python_uniqueness()
