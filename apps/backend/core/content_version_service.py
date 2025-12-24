"""
Content Version Service - Handle regenerations and A/B testing
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.content import GeneratedContent
from database.models.advanced import ContentVersion
import uuid as uuid_lib


class ContentVersionService:
    """Service for managing content versions and regenerations."""
    
    @staticmethod
    def create_version(
        db: Session,
        content_id: str,
        conversation_id: str,
        user_id: str,
        generated_content: dict,
        model_used: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        parameters: dict = None,
        seo_score: float = 0.0,
        uniqueness_score: float = 0.0,
        engagement_score: float = 0.0,
        generation_time_ms: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        parent_version_id: str = None,
        regeneration_reason: str = None,
    ) -> ContentVersion:
        """Create a new content version."""
        
        # Get next version number
        existing = db.query(ContentVersion).filter(
            ContentVersion.content_id == content_id
        ).count()
        version_number = existing + 1
        
        # Extract text from generated_content
        content_text = ""
        if isinstance(generated_content, dict):
            content_text = generated_content.get("text", "") or generated_content.get("content", "")
        
        version = ContentVersion(
            id=uuid_lib.uuid4(),
            content_id=content_id,
            conversation_id=conversation_id,
            user_id=user_id,
            version_number=version_number,
            is_selected=version_number == 1,  # First version selected by default
            generated_content=generated_content,
            content_length=len(content_text),
            content_tokens=output_tokens,
            model_used=model_used,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            parameters=parameters or {},
            seo_score=seo_score,
            uniqueness_score=uniqueness_score,
            engagement_score=engagement_score,
            generation_time_ms=generation_time_ms,
            input_tokens_used=input_tokens,
            output_tokens_used=output_tokens,
            cost_usd=cost_usd,
            parent_version_id=parent_version_id,
            regeneration_reason=regeneration_reason,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        return version
    
    @staticmethod
    def select_version(
        db: Session,
        version_id: str,
        content_id: str,
    ) -> ContentVersion:
        """Mark a version as selected."""
        
        # Deselect all other versions
        db.query(ContentVersion).filter(
            ContentVersion.content_id == content_id
        ).update({"is_selected": False})
        
        # Select this version
        version = db.query(ContentVersion).filter(
            ContentVersion.id == version_id
        ).first()
        
        if version:
            version.is_selected = True
            version.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(version)
        
        return version
    
    @staticmethod
    def rate_version(
        db: Session,
        version_id: str,
        rating: int,
        feedback: str = None,
    ) -> ContentVersion:
        """Add user rating and feedback to a version."""
        
        version = db.query(ContentVersion).filter(
            ContentVersion.id == version_id
        ).first()
        
        if version:
            version.user_rating = rating
            version.user_feedback = feedback
            version.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(version)
        
        return version
    
    @staticmethod
    def get_versions_for_content(
        db: Session,
        content_id: str,
    ) -> list[ContentVersion]:
        """Get all versions of a content."""
        
        return db.query(ContentVersion).filter(
            ContentVersion.content_id == content_id
        ).order_by(ContentVersion.version_number).all()
    
    @staticmethod
    def get_best_version(
        db: Session,
        content_id: str,
    ) -> ContentVersion:
        """Get the highest rated version of content."""
        
        return db.query(ContentVersion).filter(
            ContentVersion.content_id == content_id
        ).order_by(ContentVersion.user_rating.desc()).first()
