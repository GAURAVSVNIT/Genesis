"""
Vertex AI Multimodal Embedding service using multimodalembedding@001 model.
Uses Google Cloud Vertex AI for generating embeddings.
"""

import os
from typing import Optional, List
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic
from sqlalchemy.orm import Session
from database.models.content import ContentEmbedding, GeneratedContent
from database.database import SessionLocal
from core.config import settings


class VertexAIEmbeddingService:
    """Service for generating embeddings using Vertex AI multimodalembedding@001 model."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model: str = "multimodalembedding@001"
    ):
        """
        Initialize the Vertex AI embedding service.
        
        Args:
            project_id: GCP project ID (from environment if not provided)
            location: GCP region for Vertex AI
            model: Embedding model name (default: multimodalembedding@001)
        """
        self.project_id = project_id or settings.GCP_PROJECT_ID or os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.model_name = model
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID not found. Set it in .env file or pass as parameter.")
        
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)
        
        # Get the prediction client
        self.client_options = {"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
        self.client = gapic.PredictionServiceClient(client_options=self.client_options)
        
        # Model endpoint
        self.endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}"
        
        # Embedding dimension for multimodalembedding@001 is 1408
        self.embedding_dim = 1408

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a given text using Vertex AI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding (1408 dimensions)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Prepare the request
        from google.protobuf import struct_pb2
        
        instance = struct_pb2.Struct()
        instance.fields["text"].string_value = text
        
        instances = [instance]
        
        # Make prediction request
        response = self.client.predict(
            endpoint=self.endpoint,
            instances=instances
        )
        
        # Extract embedding from response
        # The multimodalembedding@001 returns embeddings in the predictions field
        if response.predictions:
            embedding = list(response.predictions[0].get("textEmbedding", []))
            return embedding
        else:
            raise ValueError("No embedding returned from Vertex AI")

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts at once.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each is a list of 1408 floats)
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Prepare the request
        from google.protobuf import struct_pb2
        
        instances = []
        for text in texts:
            instance = struct_pb2.Struct()
            instance.fields["text"].string_value = text
            instances.append(instance)
        
        # Make prediction request
        response = self.client.predict(
            endpoint=self.endpoint,
            instances=instances
        )
        
        # Extract embeddings from response
        embeddings = []
        for prediction in response.predictions:
            embedding = list(prediction.get("textEmbedding", []))
            embeddings.append(embedding)
        
        return embeddings

    def embed_text(self, text: str) -> list[float]:
        """
        Alias for generate_embedding for compatibility with local embeddings interface.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        return self.generate_embedding(text)

    def embed_multiple(self, texts: list[str]) -> list[list[float]]:
        """
        Alias for generate_embeddings_batch for compatibility with local embeddings interface.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        return self.generate_embeddings_batch(texts)

    def store_embedding(
        self,
        content_id: str,
        text: str,
        db: Optional[Session] = None,
        model: Optional[str] = None,
    ) -> ContentEmbedding:
        """
        Generate embedding and store it in the database.
        
        Args:
            content_id: UUID of the GeneratedContent
            text: Text to embed
            db: Database session (creates new if not provided)
            model: Embedding model name (uses default if not provided)
            
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
                embedding_model=model or self.model_name,
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
_vertex_ai_embedding_service: Optional[VertexAIEmbeddingService] = None


def get_vertex_ai_embedding_service(
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> VertexAIEmbeddingService:
    """Get or create the Vertex AI embedding service instance."""
    global _vertex_ai_embedding_service
    if _vertex_ai_embedding_service is None:
        _vertex_ai_embedding_service = VertexAIEmbeddingService(
            project_id=project_id,
            location=location
        )
    return _vertex_ai_embedding_service
