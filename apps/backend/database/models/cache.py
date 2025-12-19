"""
ChatGPT-style conversation and prompt cache schema for PostgreSQL.
Migration-ready with version tracking.
"""

from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime
import uuid


class ConversationCache(Base):
    """Cache for entire conversations (like ChatGPT's chat history)."""
    
    __tablename__ = "conversation_cache"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation metadata
    user_id = Column(String(36), nullable=True)  # Optional: for authenticated users
    session_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Auto-generated title from first prompt
    
    # Content hashing for deduplication
    conversation_hash = Column(String(64), nullable=False, unique=False, index=True)
    
    # Cache statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Metadata
    platform = Column(String(50), nullable=True)  # twitter, linkedin, instagram, etc.
    tone = Column(String(50), nullable=True)
    language = Column(String(10), default="en")
    migration_version = Column(String(20), default="1.0")  # Version tracking for migrations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For TTL management
    
    # Relationships
    messages = relationship("MessageCache", back_populates="conversation", cascade="all, delete-orphan")
    embeddings = relationship("CacheEmbedding", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes for fast lookup
    __table_args__ = (
        Index('idx_session_id_created', 'session_id', 'created_at'),
        Index('idx_user_id_accessed', 'user_id', 'accessed_at'),
        Index('idx_conversation_hash', 'conversation_hash'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "title": self.title,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
        }


class MessageCache(Base):
    """Individual messages in a cached conversation (like ChatGPT messages)."""
    
    __tablename__ = "message_cache"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversation_cache.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_hash = Column(String(64), nullable=False, index=True)  # MD5 of content
    tokens = Column(Integer, default=0)
    sequence = Column(Integer, nullable=False)  # Order in conversation
    
    # Quality metrics
    is_edited = Column(Boolean, default=False)
    quality_score = Column(Float, nullable=True)  # 0-1 rating
    migration_version = Column(String(20), default="1.0")  # Version tracking for migrations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    conversation = relationship("ConversationCache", back_populates="messages")
    
    __table_args__ = (
        Index('idx_conversation_sequence', 'conversation_id', 'sequence'),
        Index('idx_message_hash', 'message_hash'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "tokens": self.tokens,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
        }


class PromptCache(Base):
    """Cache for individual prompt-response pairs (deduplication)."""
    
    __tablename__ = "prompt_cache"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Prompt identification
    prompt_hash = Column(String(64), nullable=False, unique=True, index=True)
    prompt_text = Column(Text, nullable=False)
    
    # Response cache
    response_text = Column(Text, nullable=False)
    response_hash = Column(String(64), nullable=False, index=True)
    
    # Generation metadata
    model = Column(String(100), default="gemini-2.0-flash")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    
    # Performance metrics
    generation_time = Column(Float, nullable=True)  # seconds
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    
    # Cache statistics
    hits = Column(Integer, default=0)  # How many times this was used
    last_accessed = Column(DateTime, default=datetime.utcnow)
    migration_version = Column(String(20), default="1.0")  # Version tracking for migrations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_prompt_hash_created', 'prompt_hash', 'created_at'),
        Index('idx_last_accessed', 'last_accessed'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "prompt_hash": self.prompt_hash,
            "model": self.model,
            "hits": self.hits,
            "generation_time": self.generation_time,
            "created_at": self.created_at.isoformat(),
        }


class CacheEmbedding(Base):
    """Embeddings for cached messages (for semantic search & similarity)."""
    
    __tablename__ = "cache_embeddings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversation_cache.id"), nullable=False, index=True)
    message_id = Column(String(36), nullable=True)
    
    # Embedding data
    embedding = Column(String(5000), nullable=False)  # JSON array as string, or use pgvector
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    embedding_dim = Column(Integer, default=384)
    
    # Metadata
    text_chunk = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    migration_version = Column(String(20), default="1.0")  # Version tracking for migrations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    conversation = relationship("ConversationCache", back_populates="embeddings")
    
    __table_args__ = (
        Index('idx_conversation_embedding', 'conversation_id', 'created_at'),
    )


class CacheMetrics(Base):
    """Track cache performance metrics for optimization."""
    
    __tablename__ = "cache_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cache statistics
    total_entries = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    
    # Performance
    avg_response_time = Column(Float, default=0.0)  # milliseconds
    avg_generation_time = Column(Float, default=0.0)
    
    # Storage
    storage_size_mb = Column(Float, default=0.0)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0
    
    def to_dict(self):
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
            "avg_response_time": self.avg_response_time,
            "storage_size_mb": self.storage_size_mb,
        }


class CacheMigration(Base):
    """Track cache data migrations between backends."""
    
    __tablename__ = "cache_migrations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Migration info
    version = Column(String(20), nullable=False)  # e.g., "1.0", "1.1"
    migration_type = Column(String(50))  # 'redis_to_postgres', 'postgres_to_bigquery', etc.
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    
    # Statistics
    records_migrated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    source = Column(String(50))  # 'redis', 'postgres', 'bigquery'
    destination = Column(String(50))
    notes = Column(Text, nullable=True)
    
    def to_dict(self):
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        
        return {
            "id": self.id,
            "version": self.version,
            "migration_type": self.migration_type,
            "status": self.status,
            "records_migrated": self.records_migrated,
            "records_failed": self.records_failed,
            "duration_seconds": duration,
        }
