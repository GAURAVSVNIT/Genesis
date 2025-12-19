"""
Content Generation Models
- generated_content
- content_embeddings
- file_attachments
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from database.models.base import BaseModel, GUID, JSONEncodedList
import uuid

class GeneratedContent(BaseModel):
    """AI-generated content"""
    __tablename__ = "generated_content"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    conversation_id = Column(GUID(), nullable=True, index=True)  # No FK constraint - allows NULL for API requests
    message_id = Column(GUID(), ForeignKey("messages.id"), nullable=True)
    
    # Original Request
    original_prompt = Column(Text, nullable=False)
    requirements = Column(JSON)
    
    # Content
    content_type = Column(String(50), nullable=False)  # 'text', 'image', 'video', 'blog'
    platform = Column(String(100))  # Target platform
    generated_content = Column(JSON)  # Generated content
    
    # Quality Scores
    seo_score = Column(Float, default=0.0)  # 0-1
    uniqueness_score = Column(Float, default=0.0)  # 0-1 (plagiarism check)
    engagement_score = Column(Float, default=0.0)  # 0-1 (engagement prediction)
    
    # Publishing
    status = Column(String(20), default="draft", index=True)  # 'draft', 'published', 'archived'
    published_platforms = Column(JSON)  # Where it was published
    published_at = Column(DateTime)
    published_urls = Column(JSONEncodedList)
    
    # Tags
    tags = Column(JSONEncodedList)
    
    # Relationships
    user = relationship("User", back_populates="generated_content")
    # Note: conversation relationship removed - generated_content.conversation_id can be NULL for API requests
    embeddings = relationship("ContentEmbedding", back_populates="content", cascade="all, delete-orphan")
    file_attachments = relationship("FileAttachment", back_populates="content", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_generated_content_user', 'user_id'),
        Index('idx_generated_content_conversation', 'conversation_id'),
        Index('idx_generated_content_status', 'status'),
    )


class ContentEmbedding(BaseModel):
    """Vector embeddings for similarity search (ChatGPT RAG style)"""
    __tablename__ = "content_embeddings"
    
    content_id = Column(GUID(), ForeignKey("generated_content.id"), nullable=False, index=True)
    
    # Content Reference (like ChatGPT retrieves context)
    text_source = Column(String(50), default="generated_content")  # 'generated_content' or 'message'
    source_id = Column(GUID(), nullable=True, index=True)  # Message or Content ID
    
    # Embedded Text (for tracking what was embedded)
    embedded_text = Column(Text, nullable=False)
    text_length = Column(Integer)  # Character count
    text_tokens = Column(Integer)  # Token count
    
    # Vector Data
    embedding = Column(JSONEncodedList, nullable=False)
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    embedding_dimensions = Column(Integer, default=384)
    
    # Embedding Quality (like ChatGPT filters results)
    confidence_score = Column(Float, default=1.0)  # How confident is this embedding
    is_valid = Column(Boolean, default=True)  # If embedding passed quality checks
    
    # Relationships
    content = relationship("GeneratedContent", back_populates="embeddings")
    
    __table_args__ = (
        Index('idx_embedding_content', 'content_id'),
        Index('idx_embedding_source', 'source_id'),
        Index('idx_embedding_valid', 'is_valid'),
    )


class FileAttachment(BaseModel):
    """Track uploaded files"""
    __tablename__ = "file_attachments"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(GUID(), ForeignKey("messages.id"), nullable=True, index=True)
    content_id = Column(GUID(), ForeignKey("generated_content.id"), nullable=True, index=True)
    
    # File Info
    filename = Column(String(500), nullable=False)
    file_type = Column(String(100))  # File extension
    file_size = Column(Integer)  # Bytes
    mime_type = Column(String(100))
    
    # Storage
    storage_url = Column(Text, nullable=False)  # S3/Cloud storage URL
    storage_path = Column(String(500))  # Local path
    
    # Expiration
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="file_attachments")
    content = relationship("GeneratedContent", back_populates="file_attachments")
    
    __table_args__ = (
        Index('idx_attachments_user', 'user_id'),
        Index('idx_attachments_message', 'message_id'),
    )


class UsageMetrics(BaseModel):
    """Track usage and costs per user"""
    __tablename__ = "usage_metrics"
    
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Request Counts
    total_requests = Column(Integer, default=0)  # Total API calls
    cache_hits = Column(Integer, default=0)  # Requests served from cache
    cache_misses = Column(Integer, default=0)  # Requests that needed generation
    
    # Aggregated Metrics
    total_input_tokens = Column(Integer, default=0)  # Sum of all input tokens
    total_output_tokens = Column(Integer, default=0)  # Sum of all output tokens
    total_tokens = Column(Integer, default=0)  # Total tokens (cached + generated)
    
    # Performance
    average_response_time_ms = Column(Float, default=0.0)  # Average latency
    cache_hit_rate = Column(Float, default=0.0)  # cache_hits / total_requests
    
    # Cost (if applicable)
    total_cost = Column(Float, default=0.0)  # USD cost for API calls
    cache_cost = Column(Float, default=0.0)  # Cost of cached calls (usually lower)
    
    # Tier Info
    tier = Column(String(20), default="free")  # 'free', 'premium', 'enterprise'
    monthly_request_limit = Column(Integer, default=100)  # Rate limit
    monthly_requests_used = Column(Integer, default=0)  # Used this month
    
    # Relationships
    user = relationship("User", back_populates="usage_metrics")
    
    __table_args__ = (
        Index('idx_metrics_user', 'user_id'),
        Index('idx_metrics_tier', 'tier'),
    )


class CacheContentMapping(BaseModel):
    """Map cache entries to final content (for migrations)"""
    __tablename__ = "cache_content_mapping"
    
    # Cache Reference
    cache_type = Column(String(50), nullable=False, index=True)  # 'conversation', 'message', 'prompt'
    cache_id = Column(GUID(), nullable=False, index=True)  # ID in cache table
    
    # Content Reference
    content_id = Column(GUID(), ForeignKey("generated_content.id"), nullable=True, index=True)
    
    # User Tracking
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Migration Tracking
    cache_backend = Column(String(50), default="postgresql")  # 'redis', 'postgresql', 'firestore'
    content_backend = Column(String(50), default="postgresql")  # Where content is stored
    
    # Status
    is_synced = Column(Boolean, default=True)  # If cache and content are in sync
    last_synced_at = Column(DateTime, nullable=True)
    
    # Relationships
    content = relationship("GeneratedContent")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_mapping_cache', 'cache_id', 'cache_type'),
        Index('idx_mapping_content', 'content_id'),
        Index('idx_mapping_user', 'user_id'),
        Index('idx_mapping_synced', 'is_synced'),
    )
