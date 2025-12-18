"""
Embedding service for generating and managing vector embeddings using local Sentence-Transformers.
"""

import os
from typing import Optional
from core.local_embeddings import get_local_embedding_service
from sqlalchemy.orm import Session
from database.models.content import ContentEmbedding, GeneratedContent
from database.database import SessionLocal


class EmbeddingService:
    """Service for generating and storing embeddings using local sentence-transformers."""

    def __init__(self):
        """Initialize the embedding service with local transformers."""
        self.embedding_service = get_local_embedding_service()

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a given text using sentence-transformers.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding (384 dimensions)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Local embeddings returns a single embedding for a single text
        embedding = self.embedding_service.embed_text(text)
        return embedding

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts at once.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each is a list of 384 floats)
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Local embeddings handles batch processing
        embeddings = self.embedding_service.embed_multiple(texts)
        return embeddings

    def store_embedding(
        self,
        content_id: str,
        text: str,
        db: Optional[Session] = None,
        model: str = "all-MiniLM-L6-v2",
    ) -> ContentEmbedding:
        """
        Generate embedding and store it in the database.
        
        Args:
            content_id: UUID of the GeneratedContent
            text: Text to embed
            db: Database session (creates new if not provided)
            model: Embedding model name
            
        Returns:
            ContentEmbedding object
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Store in database
            content_embedding = ContentEmbedding(
                content_id=content_id,
                embedding=embedding,
                embedding_model=model,
            )
            
            db.add(content_embedding)
            db.commit()
            db.refresh(content_embedding)
            
            return content_embedding
        finally:
            if should_close:
                db.close()

    def find_similar_content(
        self,
        query_text: str,
        limit: int = 5,
        db: Optional[Session] = None,
    ) -> list[GeneratedContent]:
        """
        Find similar content using vector similarity search.
        
        Args:
            query_text: Text to search for similar content
            limit: Number of results to return
            db: Database session (creates new if not provided)
            
        Returns:
            List of GeneratedContent ordered by similarity
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)
            
            # Use pgvector cosine similarity (<-> operator)
            # This finds the most similar embeddings
            from sqlalchemy import func, text as sql_text
            
            similar_embeddings = db.query(
                ContentEmbedding,
                func.power(
                    1 - func.cast(
                        ContentEmbedding.embedding.op('<->')(query_embedding),
                        float
                    ),
                    2
                ).label('similarity')
            ).order_by(sql_text('similarity DESC')).limit(limit).all()
            
            # Extract the GeneratedContent objects
            similar_content = [
                db.query(GeneratedContent)
                .filter(GeneratedContent.id == embedding.ContentEmbedding.content_id)
                .first()
                for embedding, _ in similar_embeddings
            ]
            
            return [c for c in similar_content if c is not None]
        finally:
            if should_close:
                db.close()

    def update_embedding(
        self,
        content_id: str,
        text: str,
        db: Optional[Session] = None,
    ) -> ContentEmbedding:
        """
        Update embedding for existing content.
        
        Args:
            content_id: UUID of the GeneratedContent
            text: New text to embed
            db: Database session (creates new if not provided)
            
        Returns:
            Updated ContentEmbedding object
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # Delete old embedding
            db.query(ContentEmbedding).filter(
                ContentEmbedding.content_id == content_id
            ).delete()
            
            # Generate and store new embedding
            return self.store_embedding(content_id, text, db)
        finally:
            if should_close:
                db.close()


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
