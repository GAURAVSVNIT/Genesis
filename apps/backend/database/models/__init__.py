# database/models/__init__.py
"""
Import all models to make them available
"""
from database.models.base import BaseModel, SoftDeleteModel
from database.models.user import User, UserSettings, APIKey
from database.models.conversation import Conversation, ConversationFolder, Message
from database.models.content import GeneratedContent, ContentEmbedding, FileAttachment, UsageMetrics, CacheContentMapping
from database.models.analytics import UsageStatistics, SearchHistory, ActivityLog, ConversationShare
from database.models.cache import (
    ConversationCache,
    MessageCache,
    PromptCache,
    CacheEmbedding,
    CacheMetrics,
    CacheMigration,
)

__all__ = [
    # Base
    "BaseModel",
    "SoftDeleteModel",
    # User Management
    "User",
    "UserSettings",
    "APIKey",
    # Conversations
    "Conversation",
    "ConversationFolder",
    "Message",
    # Content
    "GeneratedContent",
    "ContentEmbedding",
    "FileAttachment",
    "UsageMetrics",
    "CacheContentMapping",
    # Analytics
    "UsageStatistics",
    "SearchHistory",
    "ActivityLog",
    "ConversationShare",
    # Cache
    "ConversationCache",
    "MessageCache",
    "PromptCache",
    "CacheEmbedding",
    "CacheMetrics",
    "CacheMigration",
]
