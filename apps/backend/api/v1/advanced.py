"""
API endpoints for advanced AI agent features
- Content regeneration & versioning
- RAG search & attribution
- Message feedback & ratings
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from database.database import get_db
from core.content_version_service import ContentVersionService
from core.rag_service import RAGService
from core.message_feedback_service import MessageFeedbackService


router = APIRouter(prefix="/v1/advanced", tags=["advanced-ai"])


# ============ Pydantic Models ============

class ContentVersionRequest(BaseModel):
    """Request to create content version."""
    content_id: str
    conversation_id: str
    generated_content: dict
    model_used: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    top_p: Optional[float] = 0.9
    generation_time_ms: Optional[int] = 0
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    cost_usd: Optional[float] = 0.0


class SelectVersionRequest(BaseModel):
    """Request to select a version."""
    version_id: str


class RateVersionRequest(BaseModel):
    """Request to rate a version."""
    rating: int  # 1-5
    feedback: Optional[str] = None


class RAGSearchRequest(BaseModel):
    """Request to search similar content."""
    query: str
    limit: Optional[int] = 3
    similarity_threshold: Optional[float] = 0.5


class FeedbackRequest(BaseModel):
    """Request to add feedback to a message."""
    message_id: str
    conversation_id: str
    rating: Optional[int] = None  # 1-5 or -1/1 for thumbs
    is_helpful: Optional[bool] = None
    is_accurate: Optional[bool] = None
    is_relevant: Optional[bool] = None
    feedback_text: Optional[str] = None
    has_errors: Optional[bool] = False
    has_bias: Optional[bool] = False
    is_inappropriate: Optional[bool] = False
    issue_description: Optional[str] = None
    tags: Optional[List[str]] = None


class ThumbsFeedbackRequest(BaseModel):
    """Quick thumbs up/down feedback."""
    message_id: str
    conversation_id: str


# ============ Content Versioning Endpoints ============

@router.post("/versions/create")
async def create_content_version(
    request: ContentVersionRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Create a new version of generated content."""
    try:
        version = ContentVersionService.create_version(
            db=db,
            content_id=request.content_id,
            conversation_id=request.conversation_id,
            user_id=user_id,
            generated_content=request.generated_content,
            model_used=request.model_used,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            generation_time_ms=request.generation_time_ms,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cost_usd=request.cost_usd,
        )
        
        return {
            "status": "success",
            "version_id": str(version.id),
            "version_number": version.version_number,
            "is_selected": version.is_selected,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{content_id}")
async def get_content_versions(
    content_id: str,
    db: Session = Depends(get_db),
):
    """Get all versions of a content."""
    try:
        versions = ContentVersionService.get_versions_for_content(db, content_id)
        
        return {
            "status": "success",
            "content_id": content_id,
            "total_versions": len(versions),
            "versions": [
                {
                    "version_id": str(v.id),
                    "version_number": v.version_number,
                    "is_selected": v.is_selected,
                    "model_used": v.model_used,
                    "user_rating": v.user_rating,
                    "seo_score": v.seo_score,
                    "uniqueness_score": v.uniqueness_score,
                    "engagement_score": v.engagement_score,
                    "created_at": v.created_at.isoformat(),
                }
                for v in versions
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/select")
async def select_content_version(
    request: SelectVersionRequest,
    content_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Mark a version as selected."""
    try:
        version = ContentVersionService.select_version(
            db=db,
            version_id=request.version_id,
            content_id=content_id,
        )
        
        return {
            "status": "success",
            "version_id": str(version.id),
            "is_selected": version.is_selected,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/rate")
async def rate_content_version(
    request: RateVersionRequest,
    version_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Rate a content version."""
    try:
        version = ContentVersionService.rate_version(
            db=db,
            version_id=version_id,
            rating=request.rating,
            feedback=request.feedback,
        )
        
        return {
            "status": "success",
            "version_id": str(version.id),
            "rating": version.user_rating,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RAG Endpoints ============

@router.post("/rag/search")
async def search_similar_content(
    request: RAGSearchRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Search for similar content using RAG."""
    try:
        results = RAGService.retrieve_similar_content(
            db=db,
            query=request.query,
            user_id=user_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            use_local=True,
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results_count": len(results),
            "results": [
                {
                    "content_id": str(embedding.content_id),
                    "embedding_text": embedding.embedded_text[:500],  # First 500 chars
                    "similarity_score": similarity_score,
                    "embedding_model": embedding.embedding_model,
                    "confidence_score": embedding.confidence_score,
                }
                for embedding, similarity_score in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/sources/{message_id}")
async def get_message_sources(
    message_id: str,
    db: Session = Depends(get_db),
):
    """Get sources used for a specific message."""
    try:
        sources = RAGService.get_sources_for_message(db, message_id)
        
        return {
            "status": "success",
            "message_id": message_id,
            "sources_count": len(sources),
            "sources": [
                {
                    "source_id": str(s.id),
                    "source_type": s.source_type,
                    "source_title": s.source_title,
                    "similarity_score": s.similarity_score,
                    "relevance_score": s.relevance_score,
                    "usage_position": s.usage_position,
                    "usage_percentage": s.usage_percentage,
                }
                for s in sources
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Feedback Endpoints ============

@router.post("/feedback/add")
async def add_message_feedback(
    request: FeedbackRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Add feedback to a message."""
    try:
        feedback = MessageFeedbackService.add_feedback(
            db=db,
            message_id=request.message_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
            rating=request.rating,
            is_helpful=request.is_helpful,
            is_accurate=request.is_accurate,
            is_relevant=request.is_relevant,
            feedback_text=request.feedback_text,
            has_errors=request.has_errors,
            has_bias=request.has_bias,
            is_inappropriate=request.is_inappropriate,
            issue_description=request.issue_description,
            tags=request.tags,
        )
        
        return {
            "status": "success",
            "feedback_id": str(feedback.id),
            "rating": feedback.rating,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/thumbs-up")
async def thumbs_up(
    request: ThumbsFeedbackRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Quick thumbs up feedback."""
    try:
        feedback = MessageFeedbackService.thumbs_up(
            db=db,
            message_id=request.message_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
        )
        
        return {
            "status": "success",
            "feedback_id": str(feedback.id),
            "rating": feedback.rating,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/thumbs-down")
async def thumbs_down(
    request: ThumbsFeedbackRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Quick thumbs down feedback."""
    try:
        feedback = MessageFeedbackService.thumbs_down(
            db=db,
            message_id=request.message_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
        )
        
        return {
            "status": "success",
            "feedback_id": str(feedback.id),
            "rating": feedback.rating,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/conversation/{conversation_id}")
async def get_conversation_quality(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """Get quality metrics for a conversation."""
    try:
        metrics = MessageFeedbackService.get_conversation_quality_score(db, conversation_id)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "quality_metrics": metrics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
