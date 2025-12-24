"""
Base model classes with common fields
"""
from sqlalchemy import Column, DateTime, String, TypeDecorator, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import json
from database.database import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses String(36).
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value

class JSONEncodedList(TypeDecorator):
    """Represents a list as a JSON-encoded string for SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.loads(value)
        return []

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SoftDeleteModel(BaseModel):
    """Base model with soft delete capability"""
    __abstract__ = True
    
    deleted_at = Column(DateTime, nullable=True)
