"""
RAG (Retrieval Augmented Generation) Service
Handles semantic search, source retrieval, and attribution
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.content import ContentEmbedding
# from database.models.advanced import RAGSource
from database.models.conversation import Message
from core.embeddings import get_embedding_service
import uuid as uuid_lib
from typing import List, Tuple
import numpy as np


class RAGService:
    """Service for semantic search and source attribution."""
    
    @staticmethod
    def retrieve_similar_content(
        db: Session,
        query: str,
        user_id: str,
        limit: int = 3,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[ContentEmbedding, float]]:
        """
        Retrieve similar content using semantic search.
        
        Returns list of (embedding, similarity_score) tuples.
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(query)
            if isinstance(query_embedding, list):
                query_vector = np.array(query_embedding)
            else:
                query_vector = query_embedding
            
            # Get all valid embeddings from user
            embeddings = db.query(ContentEmbedding).join(
                ContentEmbedding.content
            ).filter(
                ContentEmbedding.is_valid == True,
                ContentEmbedding.confidence_score >= 0.7,
            ).all()
            
            if not embeddings:
                return []
            
            # Calculate similarity scores
            results = []
            for embedding in embeddings:
                if embedding.embedding:
                    stored_vector = np.array(embedding.embedding)
                    
                    # Skip if dimensions don't match (e.g. old local embeddings vs new Vertex AI)
                    if stored_vector.shape != query_vector.shape:
                        continue
                        
                    # Cosine similarity
                    similarity = np.dot(query_vector, stored_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(stored_vector) + 1e-10
                    )
                    
                    if similarity >= similarity_threshold:
                        results.append((embedding, float(similarity)))
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        
        except Exception as e:
            print(f"Error in RAG retrieval: {str(e)}")
            return []
    
    @staticmethod
    def create_rag_source(
        db: Session,
        message_id: str,
        user_id: str,
        source_type: str,
        source_id: str = None,
        source_embedding_id: str = None,
        source_title: str = None,
        source_text: str = None,
        source_url: str = None,
        similarity_score: float = 0.0,
        relevance_score: float = 0.0,
        was_used: bool = True,
        usage_position: int = 1,
        usage_percentage: float = 100.0,
        content_version_id: str = None,
    ): # -> RAGSource
        """Create a RAG source attribution record."""
        pass
        # source = RAGSource(...)
        # db.add(source)
        # db.commit()
        # db.refresh(source)
        # return source
    
    @staticmethod
    def get_sources_for_message(
        db: Session,
        message_id: str,
    ): # -> List[RAGSource]
        """Get all sources used for a specific message."""
        return []
        # return db.query(RAGSource).filter(...)
    
    @staticmethod
    def get_sources_for_conversation(
        db: Session,
        conversation_id: str,
    ): # -> List[RAGSource]
        """Get all sources used in a conversation."""
        return []
        # return db.query(RAGSource).join(...)
