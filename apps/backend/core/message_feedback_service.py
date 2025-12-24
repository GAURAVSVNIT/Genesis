"""
Message Feedback Service - Handle user ratings, feedback, and quality signals
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.advanced import MessageFeedback
from database.models.conversation import Message
import uuid as uuid_lib


class MessageFeedbackService:
    """Service for collecting and managing user feedback."""
    
    @staticmethod
    def add_feedback(
        db: Session,
        message_id: str,
        user_id: str,
        conversation_id: str,
        rating: int = None,
        is_helpful: bool = None,
        is_accurate: bool = None,
        is_relevant: bool = None,
        feedback_text: str = None,
        has_errors: bool = False,
        has_bias: bool = False,
        is_inappropriate: bool = False,
        issue_description: str = None,
        suggested_improvement: str = None,
        tags: list = None,
        content_version_id: str = None,
    ) -> MessageFeedback:
        """Create or update feedback for a message."""
        
        # Check if feedback already exists
        existing = db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id,
            MessageFeedback.user_id == user_id,
        ).first()
        
        if existing:
            # Update existing feedback
            existing.rating = rating or existing.rating
            existing.is_helpful = is_helpful if is_helpful is not None else existing.is_helpful
            existing.is_accurate = is_accurate if is_accurate is not None else existing.is_accurate
            existing.is_relevant = is_relevant if is_relevant is not None else existing.is_relevant
            existing.feedback_text = feedback_text or existing.feedback_text
            existing.has_errors = has_errors or existing.has_errors
            existing.has_bias = has_bias or existing.has_bias
            existing.is_inappropriate = is_inappropriate or existing.is_inappropriate
            existing.issue_description = issue_description or existing.issue_description
            existing.suggested_improvement = suggested_improvement or existing.suggested_improvement
            existing.tags = tags or existing.tags
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new feedback
        feedback = MessageFeedback(
            id=uuid_lib.uuid4(),
            message_id=message_id,
            content_version_id=content_version_id,
            user_id=user_id,
            conversation_id=conversation_id,
            rating=rating,
            is_helpful=is_helpful,
            is_accurate=is_accurate,
            is_relevant=is_relevant,
            feedback_text=feedback_text,
            has_errors=has_errors,
            has_bias=has_bias,
            is_inappropriate=is_inappropriate,
            issue_description=issue_description,
            suggested_improvement=suggested_improvement,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    
    @staticmethod
    def thumbs_up(
        db: Session,
        message_id: str,
        user_id: str,
        conversation_id: str,
        content_version_id: str = None,
    ) -> MessageFeedback:
        """Quick thumbs up feedback."""
        return MessageFeedbackService.add_feedback(
            db=db,
            message_id=message_id,
            user_id=user_id,
            conversation_id=conversation_id,
            rating=1,
            is_helpful=True,
            content_version_id=content_version_id,
        )
    
    @staticmethod
    def thumbs_down(
        db: Session,
        message_id: str,
        user_id: str,
        conversation_id: str,
        content_version_id: str = None,
    ) -> MessageFeedback:
        """Quick thumbs down feedback."""
        return MessageFeedbackService.add_feedback(
            db=db,
            message_id=message_id,
            user_id=user_id,
            conversation_id=conversation_id,
            rating=-1,
            is_helpful=False,
            content_version_id=content_version_id,
        )
    
    @staticmethod
    def get_feedback_for_message(
        db: Session,
        message_id: str,
    ) -> list[MessageFeedback]:
        """Get all feedback for a message."""
        
        return db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id
        ).all()
    
    @staticmethod
    def get_conversation_feedback(
        db: Session,
        conversation_id: str,
    ) -> list[MessageFeedback]:
        """Get all feedback in a conversation."""
        
        return db.query(MessageFeedback).filter(
            MessageFeedback.conversation_id == conversation_id
        ).order_by(MessageFeedback.created_at.desc()).all()
    
    @staticmethod
    def get_conversation_quality_score(
        db: Session,
        conversation_id: str,
    ) -> dict:
        """Get quality metrics for a conversation."""
        
        feedback_list = MessageFeedbackService.get_conversation_feedback(db, conversation_id)
        
        if not feedback_list:
            return {
                "total_feedback": 0,
                "helpful_rate": 0.0,
                "accuracy_rate": 0.0,
                "relevance_rate": 0.0,
                "average_rating": 0.0,
                "issues_count": 0,
            }
        
        ratings = [f.rating for f in feedback_list if f.rating is not None]
        helpful = [f for f in feedback_list if f.is_helpful is True]
        accurate = [f for f in feedback_list if f.is_accurate is True]
        relevant = [f for f in feedback_list if f.is_relevant is True]
        issues = [f for f in feedback_list if f.has_errors or f.has_bias or f.is_inappropriate]
        
        return {
            "total_feedback": len(feedback_list),
            "helpful_rate": len(helpful) / len(feedback_list),
            "accuracy_rate": len(accurate) / len(feedback_list),
            "relevance_rate": len(relevant) / len(feedback_list),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "issues_count": len(issues),
        }
