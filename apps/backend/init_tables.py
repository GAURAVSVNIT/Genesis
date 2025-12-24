"""Initialize database tables for context and checkpoints"""
import sys
sys.path.insert(0, '.')

from database.database import engine
from database.models.base import BaseModel
from database.models.conversation import Conversation, Message, BlogCheckpoint, ConversationContext

# Create all tables
BaseModel.metadata.create_all(engine)
print("✓ All tables created successfully")
print("  - blog_checkpoints")
print("  - conversation_contexts")
