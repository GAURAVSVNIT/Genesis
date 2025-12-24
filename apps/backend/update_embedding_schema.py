"""
Update the cache_embeddings table schema to support larger embeddings
"""

from database.database import SessionLocal, engine
from database.models.cache import CacheEmbedding
from sqlalchemy import text

def update_embedding_column():
    """Update the embedding column from String(5000) to Text"""
    
    db = SessionLocal()
    
    print("=" * 80)
    print("UPDATING CACHE_EMBEDDINGS TABLE SCHEMA")
    print("=" * 80)
    
    try:
        # Drop the old column constraint if exists and recreate
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'cache_embeddings'
                    )
                """)
            )
            
            if result.fetchone()[0]:
                print("\n[1] Table 'cache_embeddings' exists")
                
                # Update column type
                print("[2] Updating 'embedding' column from VARCHAR(5000) to TEXT...")
                connection.execute(
                    text("ALTER TABLE cache_embeddings ALTER COLUMN embedding TYPE TEXT")
                )
                connection.commit()
                print("[3] Column type updated successfully!")
                
                # Update default for embedding_model
                print("[4] Updating default for 'embedding_model'...")
                connection.execute(
                    text("ALTER TABLE cache_embeddings ALTER COLUMN embedding_model SET DEFAULT 'multimodalembedding@001'")
                )
                connection.commit()
                print("[5] Default updated!")
                
                # Update default for embedding_dim
                print("[6] Updating default for 'embedding_dim'...")
                connection.execute(
                    text("ALTER TABLE cache_embeddings ALTER COLUMN embedding_dim SET DEFAULT 1408")
                )
                connection.commit()
                print("[7] Default updated!")
                
                print("\n[SUCCESS] Table schema updated!")
            else:
                print("[Warning] Table 'cache_embeddings' does not exist yet")
        
        db.close()
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_embedding_column()
