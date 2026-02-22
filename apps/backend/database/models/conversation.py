"""
Conversation Models
- conversations
- conversation_folders
- messages
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from database.models.base import BaseModel, SoftDeleteModel, GUID, JSONEncodedList
import uuid

class ConversationFolder(BaseModel):
    """Organize conversations into folders"""
    __tablename__ = "conversation_folders"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    parent_folder_id = Column(GUID(), ForeignKey("conversation_folders.id"), nullable=True)
    color = Column(String(20))  # 'red', 'blue', 'green', etc.
    conversation_count = Column(Integer, default=0)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="folder")
    
    __table_args__ = (
        Index('idx_folders_user', 'user_id'),
        Index('idx_folders_parent', 'parent_folder_id'),
    )


class Conversation(SoftDeleteModel):
    """Chat sessions between user and AI"""
    __tablename__ = "conversations"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    folder_id = Column(GUID(), ForeignKey("conversation_folders.id"), nullable=True)
    
    # Basic Info
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # AI Configuration
    agent_type = Column(String(100), default="text-generation")  # 'text-generation', 'image', 'video'
    model_used = Column(String(100), default="gpt-4")  # 'gpt-4', 'claude-3', 'gemini-pro'
    system_prompt = Column(Text)
    temperature = Column(Integer, default=7)  # 0-10 scale
    max_tokens = Column(Integer)
    
    # Status & Metadata
    status = Column(String(20), default="active", index=True)  # 'active', 'archived', 'deleted'
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    
    # Sharing
    is_public = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    tags = Column(JSONEncodedList)
    
    # Timestamps
    last_message_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    folder = relationship("ConversationFolder", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_conversations_user', 'user_id'),
        Index('idx_conversations_status', 'status'),
        Index('idx_conversations_created', 'created_at'),
    )


class Message(BaseModel):
    """Individual messages in conversations"""
    __tablename__ = "messages"
    
    conversation_id = Column(GUID(), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Message Content
    role = Column(String(20), nullable=False, index=True)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # 'text', 'image', 'audio', 'video'
    
    # Metadata
    message_index = Column(Integer)  # Order in conversation
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(100))
    
    # Feedback & Flags
    user_rating = Column(Integer)  # 1-5
    is_edited = Column(Boolean, default=False)
    is_regeneration = Column(Boolean, default=False)
    parent_message_id = Column(GUID(), ForeignKey("messages.id"), nullable=True)
    flagged = Column(Boolean, default=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index('idx_messages_conversation', 'conversation_id'),
        Index('idx_messages_user', 'user_id'),
        Index('idx_messages_role', 'role'),
    )


class BlogCheckpoint(BaseModel):
    """Blog content checkpoints for version control"""
    __tablename__ = "blog_checkpoints"
    
    user_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(String(255), nullable=False, index=True)
    
    # Blog Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)  # Image associated with this version
    description = Column(Text)  # Optional description of this version
    
    # Context Snapshot
    context_snapshot = Column(JSON, nullable=True)  # Full conversation context at checkpoint time
    chat_messages_snapshot = Column(JSON, nullable=True)  # Chat messages at checkpoint time
    
    # Metadata
    version_number = Column(Integer, nullable=False)  # Sequential version number
    tone = Column(String(50))
    length = Column(String(50))
    image_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)  # Current active version
    
    # Note: Relationships disabled for string keys to avoid FK constraints
    # In production, use proper UUID keys with relationships
    
    __table_args__ = (
        Index('idx_checkpoints_user', 'user_id'),
        Index('idx_checkpoints_conversation', 'conversation_id'),
        Index('idx_checkpoints_active', 'is_active'),
        Index('idx_checkpoints_created', 'created_at'),
    )


class ConversationContext(BaseModel):
    """Stores full conversation context for production-grade persistence"""
    __tablename__ = "conversation_contexts"
    
    user_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(String(255), nullable=False, index=True)
    
    # Full Context
    messages_context = Column(JSON, nullable=False)  # All messages with metadata
    chat_context = Column(Text)  # Formatted chat context for AI
    blog_context = Column(Text)  # Current blog content for AI
    full_context = Column(Text)  # Complete enriched context for generation
    
    # Metadata
    last_updated_at = Column(DateTime, nullable=False)
    message_count = Column(Integer, default=0)
    
    # Note: Relationships disabled for string keys to avoid FK constraints
    # In production, use proper UUID keys with relationships
    
    __table_args__ = (
        Index('idx_context_user', 'user_id'),
        Index('idx_context_conversation', 'conversation_id'),
        Index('idx_context_updated', 'last_updated_at'),
    )
