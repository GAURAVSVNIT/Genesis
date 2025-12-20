"""
Example endpoints for content embedding and similarity search.
Supports both Vertex AI multimodalembedding@001 and local sentence-transformers models.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel

from database.database import get_db
from database.models.content import GeneratedContent
from core.embeddings import get_embedding_service
from core.local_embeddings import get_local_embedding_service


router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])


class CreateEmbeddingRequest(BaseModel):
    """Request to create embedding for content."""
    content_id: str
    text: str
    use_local: bool = False  # Use local embeddings instead of Vertex AI


class SimilaritySearchRequest(BaseModel):
    """Request to search for similar content."""
    query: str
    limit: int = 5
    use_local: bool = False  # Use local embeddings instead of Vertex AI


class SimilarContentResponse(BaseModel):
    """Response with similar content."""
    id: str
    original_prompt: str
    content_type: str
    seo_score: float | None
    uniqueness_score: float | None
    engagement_score: float | None


@router.post("/create")
async def create_embedding(
    request: CreateEmbeddingRequest,
    db: Session = Depends(get_db),
):
    """
    Create and store embedding for generated content.
    
    Can use either Vertex AI multimodalembedding@001 or local sentence-transformers models.
    
    Args:
        request: CreateEmbeddingRequest with content_id, text, and use_local flag
        db: Database session
        
    Returns:
        Confirmation with embedding details
    """
    try:
        # Verify content exists
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == request.content_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Choose embedding service
        if request.use_local:
            embedding_service = get_local_embedding_service()
            model_name = "all-MiniLM-L6-v2"
        else:
            embedding_service = get_embedding_service()
            model_name = "multimodalembedding@001"
        
        # Generate and store embedding
        embedding = embedding_service.store_embedding(
            content_id=request.content_id,
            text=request.text,
            db=db,
        )
        
        return {
            "status": "success",
            "content_id": str(embedding.content_id),
            "embedding_dimensions": len(embedding.embedding),
            "embedding_model": model_name,
            "message": "Embedding created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[SimilarContentResponse])
async def search_similar_content(
    request: SimilaritySearchRequest,
    db: Session = Depends(get_db),
):
    """
    Search for content similar to the query using vector similarity.
    
    Can use either Vertex AI multimodalembedding@001 or local sentence-transformers models.
    
    Args:
        request: SimilaritySearchRequest with query, limit, and use_local flag
        db: Database session
        
    Returns:
        List of similar GeneratedContent ordered by relevance
    """
    try:
        # Choose embedding service
        if request.use_local:
            embedding_service = get_local_embedding_service()
        else:
            embedding_service = get_embedding_service()
        
        similar_content = embedding_service.find_similar_content(
            query_text=request.query,
            limit=request.limit,
            db=db,
        )
        
        return [
            SimilarContentResponse(
                id=str(content.id),
                original_prompt=content.original_prompt,
                content_type=content.content_type,
                seo_score=content.seo_score,
                uniqueness_score=content.uniqueness_score,
                engagement_score=content.engagement_score,
            )
            for content in similar_content
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(use_local: bool = Query(False, description="Check local embedding service")):
    """
    Check if embedding service is available.
    
    Args:
        use_local: If True, check local service; if False, check Vertex AI
    """
    try:
        if use_local:
            embedding_service = get_local_embedding_service()
            model = "all-MiniLM-L6-v2"
        else:
            embedding_service = get_embedding_service()
            model = "multimodalembedding@001"
        
        # Try to generate a test embedding
        test_embedding = embedding_service.generate_embedding("test")
        return {
            "status": "ok",
            "embedding_dimensions": len(test_embedding),
            "model": model,
            "service": "local" if use_local else "vertex_ai",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Embedding service unavailable: {str(e)}",
        )
