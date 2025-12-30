"""
Platform Connection Models
- user_platform_connections
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from database.models.base import BaseModel, GUID
import uuid

class UserPlatformConnection(BaseModel):
    """Stores authentication tokens for external platforms"""
    __tablename__ = "user_platform_connections"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # 'linkedin', 'medium', etc.
    
    # Credentials (simple storage for now)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Profile Metadata
    platform_user_id = Column(String(255))  # e.g., LinkedIn URN 'urn:li:person:...'
    profile_name = Column(String(255))
    profile_url = Column(String(512))
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    # user relationship is defined in User model (back_populates) OR we define it here if not there.
    # User model has: conversations, generated_content, user_settings, api_keys, usage_metrics
    # It does NOT have 'platform_connections' yet. We should add it to User model or just define Foreign Key.
    # For now, we define the relationship here.
    user = relationship("User", backref="platform_connections")

    __table_args__ = (
        Index('idx_platform_user', 'user_id', 'platform', unique=True),
    )
