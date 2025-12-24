"""
Alternative embedding service using sentence-transformers (local, no API calls).
Useful when Gemini API quota is exceeded or for offline embeddings.
Supports text chunking for large messages.
"""

import os
from typing import Optional, List, Tuple
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from database.models.content import ContentEmbedding, GeneratedContent
from database.database import SessionLocal
from core.chunking import TextChunker, get_chunker


class LocalEmbeddingService:
    """Service for generating embeddings using local sentence-transformers model."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        chunk_config: str = "medium"
    ):
        """
        Initialize the local embedding service.
        
        Args:
            model_name: Hugging Face model ID
                - "all-MiniLM-L6-v2": 384 dimensions, fastest
                - "all-mpnet-base-v2": 768 dimensions, better quality
                - "paraphrase-MiniLM-L6-v2": 384 dimensions, good for paraphrase
            chunk_config: Chunking strategy ('small', 'medium', 'large', 'xlarge')
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.chunker = get_chunker(chunk_config)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        embedding = self.model.encode(text, convert_to_numpy=False)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts at once (more efficient).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        embeddings = self.model.encode(texts, convert_to_numpy=False)
        return [emb.tolist() for emb in embeddings]

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks (for large messages).
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        return self.chunker.split_text(text)

    def chunk_text_with_position(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks with position metadata.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of (chunk_text, start_pos, end_pos) tuples
        """
        return self.chunker.split_with_metadata(text)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (1 token ≈ 4 characters).
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return self.chunker.estimate_tokens(text)

    def store_embedding_chunked(
        self,
        content_id: str,
        text: str,
        text_source: str = "generated_content",
        db: Optional[Session] = None,
    ) -> List[ContentEmbedding]:
        """
        Generate embeddings for chunked text and store in database.
        
        Args:
            content_id: UUID of the GeneratedContent
            text: Text to chunk and embed
            text_source: Source type ('generated_content' or 'message')
            db: Database session (creates new if not provided)
            
        Returns:
            List of ContentEmbedding objects (one per chunk)
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # Split text into chunks
            chunks = self.chunk_text_with_position(text)
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk[0] for chunk in chunks]
            embeddings = self.generate_embeddings_batch(chunk_texts)
            
            # Store each chunk embedding
            stored_embeddings = []
            for i, (chunk_text, start_pos, end_pos) in enumerate(chunks):
                content_embedding = ContentEmbedding(
                    content_id=content_id,
                    embedded_text=chunk_text,
                    text_source=text_source,
                    text_length=len(chunk_text),
                    text_tokens=self.estimate_tokens(chunk_text),
                    embedding=embeddings[i],
                    embedding_model=self.model_name,
                    embedding_dimensions=self.embedding_dim,
                    confidence_score=1.0,
                    is_valid=True,
                )
                
                db.add(content_embedding)
                stored_embeddings.append(content_embedding)
            
            db.commit()
            return stored_embeddings
        finally:
            if should_close:
                db.close()

    def store_embedding(
        self,
        content_id: str,
        text: str,
        db: Optional[Session] = None,
    ) -> ContentEmbedding:
        """
        Generate embedding and store it in the database.
        
        Args:
            content_id: UUID of the GeneratedContent
            text: Text to embed
            db: Database session (creates new if not provided)
            
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
                embedding_model=self.model_name,
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
            
            # Use pgvector cosine similarity
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
_local_embedding_service: Optional[LocalEmbeddingService] = None


def get_local_embedding_service(
    model: str = "all-MiniLM-L6-v2"
) -> LocalEmbeddingService:
    """Get or create the local embedding service instance."""
    global _local_embedding_service
    if _local_embedding_service is None:
        _local_embedding_service = LocalEmbeddingService(model_name=model)
    return _local_embedding_service
