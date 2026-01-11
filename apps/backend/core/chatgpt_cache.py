"""
Advanced caching service with Redis (hot) + PostgreSQL (persistent) support.
ChatGPT-style conversation caching with migration capabilities.
"""

import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from core.upstash_redis import RedisManager
from database.models.cache import (
    ConversationCache,
    MessageCache,
    PromptCache,
    CacheEmbedding,
    CacheMetrics,
)
import uuid


class ChatGPTStyleCache:
    """
    Hybrid caching service (Redis + PostgreSQL).
    
    Strategy:
    1. Hot cache (Redis): Recent conversations, frequently accessed prompts
    2. Cold storage (PostgreSQL): Historical data, for analytics
    3. Auto-promotion: Popular cached items stay in Redis
    """
    
    def __init__(self, db: Session = None, redis_hot_ttl: int = 3600):
        """
        Initialize cache service.
        
        Args:
            db: SQLAlchemy session for PostgreSQL
            redis_hot_ttl: Redis TTL in seconds (default 1 hour)
        """
        self.redis = RedisManager.get_instance()
        self.db = db
        self.redis_hot_ttl = redis_hot_ttl
    
    # ============ CONVERSATION CACHING ============
    
    def cache_conversation(
        self,
        session_id: str,
        messages: List[Dict],
        user_id: Optional[str] = None,
        platform: str = "general",
        tone: str = "neutral",
        title: Optional[str] = None,
    ) -> str:
        """
        Cache an entire conversation (ChatGPT-style).
        
        Args:
            session_id: Unique session identifier
            messages: List of {"role": "user"|"assistant", "content": "..."}
            user_id: Optional user ID
            platform: Content platform (twitter, linkedin, etc)
            tone: Content tone
            title: Conversation title
            
        Returns:
            conversation_id for future reference
        """
        
        conversation_id = str(uuid.uuid4())
        conversation_hash = self._hash_messages(messages)
        
        # Prepare conversation data
        conv_data = {
            "id": conversation_id,
            "user_id": user_id,
            "session_id": session_id,
            "title": title,
            "conversation_hash": conversation_hash,
            "message_count": len(messages),
            "platform": platform,
            "tone": tone,
            "messages": messages,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # 1. Store in Redis (hot cache)
        redis_key = f"conv:hot:{conversation_id}"
        self.redis.setex(redis_key, self.redis_hot_ttl, json.dumps(conv_data))
        
        # 2. Store in PostgreSQL (persistent)
        if self.db:
            try:
                # Create conversation record
                db_conv = ConversationCache(
                    id=conversation_id,
                    user_id=user_id,
                    session_id=session_id,
                    title=title,
                    conversation_hash=conversation_hash,
                    message_count=len(messages),
                    platform=platform,
                    tone=tone,
                )
                self.db.add(db_conv)
                
                # Create message records
                for idx, msg in enumerate(messages):
                    db_msg = MessageCache(
                        conversation_id=conversation_id,
                        role=msg["role"],
                        content=msg["content"],
                        message_hash=hashlib.md5(msg["content"].encode()).hexdigest(),
                        tokens=self._estimate_tokens(msg["content"]),
                        sequence=idx,
                    )
                    self.db.add(db_msg)
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print(f"PostgreSQL save error: {e}")
        
        # 3. Add to index for quick lookup
        self._add_to_index(session_id, conversation_id)
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Retrieve cached conversation (tries Redis first, then PostgreSQL).
        
        Returns:
            Conversation dict or None
        """
        
        # 1. Try hot cache (Redis)
        redis_key = f"conv:hot:{conversation_id}"
        cached = self.redis.get(redis_key)
        
        if cached:
            # Refresh TTL on access
            self.redis.expire(redis_key, self.redis_hot_ttl)
            return json.loads(cached)
        
        # 2. Try cold storage (PostgreSQL)
        if self.db:
            try:
                conv = self.db.query(ConversationCache).filter_by(id=conversation_id).first()
                if conv:
                    # Get messages
                    messages = self.db.query(MessageCache)\
                        .filter_by(conversation_id=conversation_id)\
                        .order_by(MessageCache.sequence)\
                        .all()
                    
                    conv_data = conv.to_dict()
                    conv_data["messages"] = [msg.to_dict() for msg in messages]
                    
                    # Promote back to Redis
                    self.redis.setex(redis_key, self.redis_hot_ttl, json.dumps(conv_data))
                    
                    return conv_data
            except Exception as e:
                print(f"PostgreSQL read error: {e}")
        
        return None
    
    # ============ PROMPT-RESPONSE CACHING ============
    
    def cache_prompt_response(
        self,
        prompt: str,
        response: str,
        model: str = "gemini-2.5-flash",
        generation_time: Optional[float] = None,
        tokens: Dict[str, int] = None,
    ) -> str:
        """
        Cache a prompt-response pair (for deduplication).
        
        Args:
            prompt: User prompt
            response: Generated response
            model: LLM model used
            generation_time: Time taken to generate (seconds)
            tokens: {"input": 100, "output": 200}
            
        Returns:
            cache_id
        """
        
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_id = str(uuid.uuid4())
        tokens = tokens or {}
        
        cache_data = {
            "id": cache_id,
            "prompt_hash": prompt_hash,
            "prompt": prompt,
            "response": response,
            "model": model,
            "generation_time": generation_time,
            "tokens": tokens,
            "hits": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # 1. Store in Redis
        redis_key = f"prompt:{prompt_hash}"
        self.redis.setex(redis_key, self.redis_hot_ttl, json.dumps(cache_data))
        
        # 2. Store in PostgreSQL
        if self.db:
            try:
                db_cache = PromptCache(
                    id=cache_id,
                    prompt_hash=prompt_hash,
                    prompt_text=prompt,
                    response_text=response,
                    response_hash=hashlib.md5(response.encode()).hexdigest(),
                    model=model,
                    generation_time=generation_time,
                    input_tokens=tokens.get("input", 0),
                    output_tokens=tokens.get("output", 0),
                )
                self.db.add(db_cache)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print(f"Prompt cache save error: {e}")
        
        return cache_id
    
    def get_cached_prompt(self, prompt: str) -> Optional[Dict]:
        """
        Check if prompt already cached (deduplication).
        
        Returns:
            Cached response or None
        """
        
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        redis_key = f"prompt:{prompt_hash}"
        
        # Try Redis first
        cached = self.redis.get(redis_key)
        if cached:
            data = json.loads(cached)
            # Increment hits
            if self.db:
                try:
                    prompt_cache = self.db.query(PromptCache)\
                        .filter_by(prompt_hash=prompt_hash).first()
                    if prompt_cache:
                        prompt_cache.hits += 1
                        prompt_cache.last_accessed = datetime.utcnow()
                        self.db.commit()
                except:
                    pass
            return data
        
        # Try PostgreSQL
        if self.db:
            try:
                prompt_cache = self.db.query(PromptCache)\
                    .filter_by(prompt_hash=prompt_hash).first()
                
                if prompt_cache:
                    # Update access metrics
                    prompt_cache.hits += 1
                    prompt_cache.last_accessed = datetime.utcnow()
                    
                    # Promote to Redis if popular
                    if prompt_cache.hits > 5:
                        cache_data = {
                            "id": prompt_cache.id,
                            "prompt": prompt_cache.prompt_text,
                            "response": prompt_cache.response_text,
                            "model": prompt_cache.model,
                            "hits": prompt_cache.hits,
                        }
                        self.redis.setex(redis_key, self.redis_hot_ttl, json.dumps(cache_data))
                    
                    self.db.commit()
                    
                    return {
                        "response": prompt_cache.response_text,
                        "model": prompt_cache.model,
                        "hits": prompt_cache.hits,
                    }
            except Exception as e:
                print(f"Prompt read error: {e}")
        
        return None
    
    # ============ HELPER METHODS ============
    
    def _hash_messages(self, messages: List[Dict]) -> str:
        """Generate hash of conversation messages."""
        combined = json.dumps(messages, sort_keys=True)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough: ~4 characters per token
        return len(text) // 4
    
    def _add_to_index(self, session_id: str, conversation_id: str):
        """Add conversation to session index for quick lookup."""
        index_key = f"sessions:{session_id}"
        try:
            conversations = self.redis.get(index_key)
            if conversations:
                conv_list = json.loads(conversations)
            else:
                conv_list = []
            
            if conversation_id not in conv_list:
                conv_list.append(conversation_id)
                self.redis.setex(index_key, 86400, json.dumps(conv_list))  # 24 hour TTL
        except Exception as e:
            print(f"Index update error: {e}")
    
    # ============ MIGRATION SUPPORT ============
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        try:
            redis_info = self.redis.info()
            
            metrics = {
                "redis_memory_used": redis_info.get("used_memory_human", "N/A"),
                "redis_keys": redis_info.get("db0", {}).get("keys", 0) if isinstance(redis_info.get("db0"), dict) else 0,
            }
            
            if self.db:
                try:
                    conv_count = self.db.query(ConversationCache).count()
                    msg_count = self.db.query(MessageCache).count()
                    prompt_count = self.db.query(PromptCache).count()
                    
                    metrics.update({
                        "postgres_conversations": conv_count,
                        "postgres_messages": msg_count,
                        "postgres_cached_prompts": prompt_count,
                    })
                except:
                    pass
            
            return metrics
        except Exception as e:
            print(f"Metrics error: {e}")
            return {}
    
    def export_for_migration(self, start_date: Optional[datetime] = None) -> List[Dict]:
        """
        Export cache data for migration to another backend.
        
        Args:
            start_date: Only export data after this date
            
        Returns:
            List of conversation records
        """
        
        if not self.db:
            return []
        
        try:
            query = self.db.query(ConversationCache)
            if start_date:
                query = query.filter(ConversationCache.created_at >= start_date)
            
            conversations = query.all()
            exported = []
            
            for conv in conversations:
                messages = self.db.query(MessageCache)\
                    .filter_by(conversation_id=conv.id)\
                    .order_by(MessageCache.sequence)\
                    .all()
                
                conv_data = conv.to_dict()
                conv_data["messages"] = [msg.to_dict() for msg in messages]
                exported.append(conv_data)
            
            return exported
        except Exception as e:
            print(f"Export error: {e}")
            return []
