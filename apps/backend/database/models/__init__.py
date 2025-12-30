# database/models/__init__.py
"""
Import all models to make them available
"""
from database.models.base import BaseModel, SoftDeleteModel
from database.models.user import User, UserSettings, APIKey
from database.models.conversation import Conversation, ConversationFolder, Message
from database.models.content import GeneratedContent, ContentEmbedding, UsageMetrics
from database.models.cache import (
    ConversationCache,
    MessageCache,
    PromptCache,
    CacheEmbedding,
    CacheMetrics,
)
from database.models.platform import UserPlatformConnection

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
    "UsageMetrics",
    # Cache
    "ConversationCache",
    "MessageCache",
    "PromptCache",
    "CacheEmbedding",
    "CacheMetrics",
]
