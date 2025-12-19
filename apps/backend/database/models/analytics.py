"""
Analytics & History Models
- usage_statistics
- search_history
- activity_logs
- conversation_shares
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from database.models.base import BaseModel, GUID
import uuid

class UsageStatistics(BaseModel):
    """Track usage and billing"""
    __tablename__ = "usage_statistics"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Usage Metrics
    tokens_used = Column(Integer, default=0)
    conversations_created = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Model & Cost
    model_used = Column(String(100))
    cost_usd = Column(Float, default=0.0)
    
    # Period
    period = Column(String(20))  # 'daily', 'monthly', 'yearly'
    period_start = Column(Date)
    period_end = Column(Date)
    
    # Relationships
    user = relationship("User", back_populates="usage_statistics")
    
    __table_args__ = (
        Index('idx_usage_user', 'user_id'),
        Index('idx_usage_period', 'period', 'period_start'),
    )


class SearchHistory(BaseModel):
    """Track user searches"""
    __tablename__ = "search_history"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    source = Column(String(50))  # 'conversation', 'api', 'web'
    
    # Relationships
    user = relationship("User", back_populates="search_history")
    
    __table_args__ = (
        Index('idx_search_history_user', 'user_id'),
        Index('idx_search_history_created', 'created_at'),
    )


class ActivityLog(BaseModel):
    """Audit trail for all user actions"""
    __tablename__ = "activity_logs"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Action Details
    action = Column(String(100), nullable=False, index=True)  # 'create', 'update', 'delete', 'publish'
    resource_type = Column(String(100))  # 'conversation', 'message', 'content'
    resource_id = Column(GUID())
    
    # Changes
    changes = Column(JSON)  # What changed
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    status = Column(String(20))  # 'success', 'failure'
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    __table_args__ = (
        Index('idx_activity_logs_user', 'user_id'),
        Index('idx_activity_logs_action', 'action'),
        Index('idx_activity_logs_created', 'created_at'),
    )


class ConversationShare(BaseModel):
    """Track shared conversations"""
    __tablename__ = "conversation_shares"
    
    conversation_id = Column(GUID(), ForeignKey("conversations.id"), nullable=False, index=True)
    shared_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    shared_with_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    
    # Share Details
    share_token = Column(String(255), unique=True, nullable=False)  # Public share link
    access_level = Column(String(50), default="view")  # 'view', 'comment', 'edit'
    is_public = Column(Boolean, default=False)
    
    # Expiration & Tracking
    expires_at = Column(DateTime)
    view_count = Column(Integer, default=0)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="shares")
    
    __table_args__ = (
        Index('idx_shares_conversation', 'conversation_id'),
        Index('idx_shares_shared_by', 'shared_by_user_id'),
        Index('idx_shares_shared_with', 'shared_with_user_id'),
    )
