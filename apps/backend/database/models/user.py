"""
User Management Models
- users
- user_settings
- api_keys
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.models.base import BaseModel, SoftDeleteModel, GUID
import uuid

class User(SoftDeleteModel):
    """User account model"""
    __tablename__ = "users"
    
    # Basic Info
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    
    # Status
    status = Column(String(20), default="active", index=True)  # 'active', 'suspended', 'deleted'
    account_type = Column(String(20), default="free")  # 'free', 'pro', 'enterprise'
    language = Column(String(10), default="en")
    theme = Column(String(20), default="light")  # 'light', 'dark'
    
    # Verification & Subscription
    email_verified = Column(Boolean, default=False)
    subscription_status = Column(String(20), default="free", index=True)
    
    # Timestamps
    last_login = Column(DateTime)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="user", cascade="all, delete-orphan")
    user_settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_metrics = relationship("UsageMetrics", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_status', 'status'),
        Index('idx_users_subscription', 'subscription_status'),
    )


class UserSettings(BaseModel):
    """User preferences and settings"""
    __tablename__ = "user_settings"
    
    user_id = Column(GUID(), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Preferences
    theme = Column(String(20), default="light")
    notify_on_response = Column(Boolean, default=True)
    data_sharing_enabled = Column(Boolean, default=False)
    content_filter_level = Column(String(50), default="moderate")  # 'strict', 'moderate', 'lenient'
    
    # API Configuration
    default_model = Column(String(100), default="gpt-4")
    default_temperature = Column(Integer, default=7)  # 0-10 scale
    api_rate_limit_per_minute = Column(Integer, default=100)
    
    # Relationships
    user = relationship("User", back_populates="user_settings")


class APIKey(BaseModel):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_preview = Column(String(20))  # Last 4 chars
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_api_keys_user', 'user_id'),
        Index('idx_api_keys_active', 'is_active'),
    )
