"""
Content Generation API using Vertex AI and LangGraph.
Includes rate limiting, caching, and response tracking.

Database Integration:
- Cache Tables: conversation_cache, message_cache, prompt_cache, cache_embeddings, cache_metrics
- Main Tables: generated_content, content_embeddings, usage_metrics
- Tracking: cache_content_mapping
"""

import hashlib
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import re

from graph.content_agent import create_agent
from core.rate_limiter import RATE_LIMITERS
from core.response_cache import CACHES
from database.database import SessionLocal
from database.models.cache import (
    ConversationCache,
    MessageCache,
    PromptCache,
    CacheMetrics,
)
from database.models.content import (
    GeneratedContent,
    UsageMetrics,
    CacheContentMapping,
    ContentEmbedding,
)
from database.models.conversation import Conversation, Message


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== QUALITY SCORE CALCULATION ==========

def calculate_seo_score(content: str) -> float:
    """
    Calculate SEO score (0-1) based on content quality.
    Simple heuristics: length, keyword density, structure.
    """
    if not content:
        return 0.0
    
    # Length score (optimal: 500-2000 words)
    words = len(content.split())
    if words < 100:
        length_score = 0.2
    elif words < 300:
        length_score = 0.5
    elif words < 2000:
        length_score = 1.0
    elif words < 3000:
        length_score = 0.8
    else:
        length_score = 0.5
    
    # Structure score (has paragraphs, punctuation)
    has_structure = "\n" in content or ". " in content
    structure_score = 0.8 if has_structure else 0.4
    
    # Keyword density (simple check for variety)
    unique_words = len(set(content.lower().split()))
    total_words = len(content.split())
    keyword_score = min(1.0, unique_words / max(total_words / 10, 1))
    
    # Average the scores
    seo_score = (length_score + structure_score + keyword_score) / 3
    return round(min(1.0, seo_score), 2)


def calculate_uniqueness_score(content: str, prompt: str) -> float:
    """
    Calculate uniqueness score (0-1) based on content vs prompt overlap.
    Lower overlap = higher uniqueness = higher score.
    """
    if not content or not prompt:
        return 0.8
    
    # Simple overlap detection: what % of prompt appears in content
    prompt_lower = prompt.lower()
    content_lower = content.lower()
    
    # Count how many prompt words appear in content
    prompt_words = set(prompt_lower.split())
    content_words = set(content_lower.split())
    
    overlap = len(prompt_words & content_words) / len(prompt_words) if prompt_words else 0
    
    # More overlap = less unique
    uniqueness_score = 1.0 - overlap
    return round(max(0.0, min(1.0, uniqueness_score)), 2)


def calculate_engagement_score(content: str) -> float:
    """
    Calculate predicted engagement score (0-1).
    Heuristics: emotional words, questions, calls-to-action, variety.
    """
    if not content:
        return 0.0
    
    content_lower = content.lower()
    
    # Emotional words (positive indicators)
    emotional_words = [
        'amazing', 'awesome', 'incredible', 'powerful', 'beautiful',
        'love', 'excellent', 'fantastic', 'revolutionary', 'unique',
        'transform', 'discover', 'unlock', 'master', 'proven'
    ]
    emotional_count = sum(1 for word in emotional_words if word in content_lower)
    emotional_score = min(1.0, emotional_count / 10)
    
    # Questions (engagement trigger)
    question_score = 0.3 if "?" in content else 0.1
    
    # Call-to-action words
    cta_words = ['click', 'learn', 'join', 'start', 'get', 'download', 'subscribe', 'try']
    cta_count = sum(1 for word in cta_words if word in content_lower)
    cta_score = min(1.0, cta_count / 5)
    
    # Length variety (short and long sentences)
    sentences = content.split(".")
    if sentences:
        sentence_lengths = [len(s.split()) for s in sentences]
        variety = len(set(sentence_lengths)) / max(len(sentences), 1)
        variety_score = min(1.0, variety)
    else:
        variety_score = 0.5
    
    # Average the scores
    engagement_score = (emotional_score + question_score + cta_score + variety_score) / 4
    return round(min(1.0, engagement_score), 2)


# ========== EMBEDDING GENERATION ==========

def generate_embedding(content: str) -> List[float]:
    """
    Generate embedding vector for content.
    Uses a lightweight model for fast inference.
    """
    try:
        # Try to use sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(content, convert_to_tensor=False)
            return embedding.tolist()
        except ImportError:
            # Fallback: Create simple embedding from word frequency
            # This is a simple hash-based embedding (not ideal but works)
            words = content.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Create a 384-dimensional vector (matching all-MiniLM-L6-v2 dimensions)
            embedding = [0.0] * 384
            for i, (word, freq) in enumerate(word_freq.items()):
                embedding[i % 384] += (freq / len(words))
            
            # Normalize
            magnitude = sum(x**2 for x in embedding) ** 0.5
            if magnitude > 0:
                embedding = [x / magnitude for x in embedding]
            
            return embedding
    except Exception as e:
        # Fallback: Return zero vector
        print(f"Embedding generation failed: {e}")
        return [0.0] * 384


# ========== COST CALCULATION ==========

PRICING = {
    "gemini-2.0-flash": {
        "input_cost_per_1k": 0.00075,   # $0.00075 per 1K input tokens
        "output_cost_per_1k": 0.003,    # $0.003 per 1K output tokens
    },
    "gemini-1.5-pro": {
        "input_cost_per_1k": 0.0025,
        "output_cost_per_1k": 0.01,
    },
    "gemini-1.5-flash": {
        "input_cost_per_1k": 0.00075,
        "output_cost_per_1k": 0.003,
    },
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost of API call based on model and token usage.
    Returns cost in USD.
    """
    pricing = PRICING.get(model, PRICING["gemini-2.0-flash"])
    
    input_cost = (input_tokens / 1000) * pricing["input_cost_per_1k"]
    output_cost = (output_tokens / 1000) * pricing["output_cost_per_1k"]
    
    total_cost = input_cost + output_cost
    return round(total_cost, 6)  # Round to 6 decimal places

router = APIRouter(prefix="/v1/content", tags=["content"])


class Message(BaseModel):
    """Message in conversation."""
    role: str  # 'user' or 'assistant'
    content: str


class GenerateContentRequest(BaseModel):
    """Request to generate content."""
    prompt: str
    conversation_history: Optional[List[Message]] = None
    safety_level: str = "moderate"  # 'strict', 'moderate', 'permissive'


class GenerateContentResponse(BaseModel):
    """Response with generated content and complete metadata."""
    success: bool
    content: str
    safety_checks: dict
    tokens_used: Optional[int] = None
    rate_limit_remaining: int = 0
    rate_limit_reset_after: int = 0
    # Caching info
    cached: bool = False
    cache_hit_rate: Optional[float] = None
    generation_time_ms: int = 0
    # ✅ Quality Scores (0-1)
    seo_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    engagement_score: Optional[float] = None
    # ✅ Cost Tracking
    cost_usd: Optional[float] = None
    total_cost_usd: Optional[float] = None


class AgentConfig(BaseModel):
    """Configuration for the agent."""
    gcp_project_id: Optional[str] = None
    model: str = "gemini-2.0-flash"
    safety_level: str = "moderate"


# Agent instance
_agent = None


def get_agent(config: AgentConfig):
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        _agent = create_agent(
            gcp_project_id=config.gcp_project_id,
            model=config.model,
            safety_level=config.safety_level,
        )
    return _agent


def normalize_prompt(prompt: str) -> str:
    """Normalize prompt for consistent hashing."""
    # Convert to lowercase
    normalized = prompt.lower()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def hash_prompt(prompt: str) -> str:
    """Create SHA256 hash of normalized prompt."""
    normalized = normalize_prompt(prompt)
    return hashlib.sha256(normalized.encode()).hexdigest()


def get_or_create_usage_metrics(db, user_id: str, tier: str = "free"):
    """Get or create usage metrics for user. Returns None for guest users."""
    if user_id is None:
        return None  # No metrics for guest/API requests
    
    metrics = db.query(UsageMetrics).filter_by(user_id=user_id).first()
    
    if not metrics:
        metrics = UsageMetrics(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tier=tier,
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            average_response_time_ms=0.0,
            cache_hit_rate=0.0,
            total_cost=0.0,
            cache_cost=0.0,
            monthly_request_limit=100 if tier == "free" else 1000,
            monthly_requests_used=0,
        )
        db.add(metrics)
        db.commit()
    
    return metrics


def get_or_create_cache_metrics(db):
    """Get or create aggregate cache metrics."""
    metrics = db.query(CacheMetrics).first()
    
    if not metrics:
        metrics = CacheMetrics(
            id=str(uuid.uuid4()),
            total_entries=0,
            cache_hits=0,
            cache_misses=0,
        )
        db.add(metrics)
        db.commit()
    
    return metrics


@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    http_request: Request,
    db = Depends(get_db)
):
    """
    Generate content using Vertex AI and LangGraph.
    
    Complete workflow:
    1. Rate limit check
    2. Prompt hash and uniqueness check
    3. Check prompt_cache for exact matches
    4. If hit: return cached response
    5. If miss: generate via Vertex AI
    6. Store in conversation_cache + message_cache
    7. Store in prompt_cache (deduplication)
    8. Store in generated_content (main table)
    9. Link in cache_content_mapping
    10. Update usage_metrics + cache_metrics
    
    Args:
        request: GenerateContentRequest
        http_request: FastAPI Request
        db: Database session
        
    Returns:
        GenerateContentResponse with complete caching info
    """
    import time
    start_time = time.time()
    
    try:
        # ========== INITIALIZATION ==========
        user_metrics = None  # Initialize for all paths
        elapsed_ms = 0
        
        # ========== STEP 1: RATE LIMITING ==========
        identifier = "guest"
        user_id = None  # For guest requests
        is_premium = False
        
        client_ip = http_request.client.host if http_request.client else "unknown"
        identifier = client_ip
        
        limiter = RATE_LIMITERS["free_user"]
        allowed, remaining, reset_after = limiter.check_rate_limit(identifier, is_premium)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {reset_after} seconds."
            )
        
        # ========== STEP 2: PROMPT HASHING & NORMALIZATION ==========
        prompt_hash = hash_prompt(request.prompt)
        
        # ========== STEP 3: CHECK PROMPT CACHE FOR EXACT MATCH ==========
        cached_prompt = db.query(PromptCache)\
            .filter_by(prompt_hash=prompt_hash)\
            .first()
        
        if cached_prompt:
            # ✅ CACHE HIT! Store in generated_content for tracking
            cached_prompt.hits += 1
            
            # Store cache hit in generated_content table
            generated_content = GeneratedContent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                conversation_id=None,
                message_id=None,
                original_prompt=request.prompt,
                requirements={"safety_level": request.safety_level},
                content_type="text",
                platform="api",
                generated_content={
                    "text": cached_prompt.response_text,
                    "model": "gemini-2.0-flash",
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "cache"
                },
                status="cached",
                created_at=datetime.utcnow()
            )
            db.add(generated_content)
            
            # Update metrics (only for authenticated users)
            user_metrics = get_or_create_usage_metrics(db, user_id, tier="free" if not is_premium else "premium")
            if user_metrics:
                user_metrics.total_requests += 1
                user_metrics.cache_hits += 1
                user_metrics.monthly_requests_used += 1
                
                if user_metrics.total_requests > 0:
                    user_metrics.cache_hit_rate = user_metrics.cache_hits / user_metrics.total_requests
            
            cache_metrics = get_or_create_cache_metrics(db)
            cache_metrics.cache_hits += 1
            # hit_rate is a computed property, no need to set it
            
            db.commit()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return GenerateContentResponse(
                success=True,
                content=cached_prompt.response_text,
                safety_checks={
                    "status": "cached",
                    "source": "prompt_cache"
                },
                tokens_used=cached_prompt.input_tokens + cached_prompt.output_tokens,
                rate_limit_remaining=remaining,
                rate_limit_reset_after=0,
                cached=True,
                cache_hit_rate=user_metrics.cache_hit_rate if user_metrics else 0.0,
                generation_time_ms=elapsed_ms
            )
        
        # ========== STEP 4: GENERATE NEW CONTENT (CACHE MISS) ==========
        config = AgentConfig(
            model="gemini-2.0-flash",
            safety_level=request.safety_level,
        )
        agent = get_agent(config)
        
        # Convert conversation history
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=msg.content))
        
        # Generate content
        content = agent.invoke(
            user_message=request.prompt,
            conversation_history=history,
        )
        
        # Get safety report
        safety_report = agent.guardrails.get_safety_report(request.prompt)
        
        # ========== STEP 5-6: STORE IN CONVERSATION & MESSAGE CACHE ==========
        conversation_id = str(uuid.uuid4())
        # Generate conversation hash from prompt
        conversation_hash = hashlib.sha256(request.prompt.encode()).hexdigest()[:64]
        
        # Generate message IDs for cache
        user_message_id = str(uuid.uuid4())
        assistant_message_id = str(uuid.uuid4())
        
        # ========== CREATE MAIN CONVERSATION & MESSAGE ENTRIES (ONLY FOR AUTHENTICATED USERS) ==========
        if user_id is not None:  # Only if authenticated
            real_conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=request.prompt[:100],  # First 100 chars as title
                description=None,
                agent_type="text-generation",
                model_used="gemini-2.0-flash",
                system_prompt=None,
                temperature=7,  # Default
                max_tokens=None,
                status="active",
                message_count=len(history) + 2,  # user + assistant messages
                token_count=0,  # Will be calculated
                is_public=False,
                is_shared=False,
                tags=[],
                last_message_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(real_conversation)
            db.flush()  # Get ID
            
            # ========== CREATE MAIN MESSAGE TABLE ENTRIES ==========
            user_message_main = Message(
                id=user_message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=request.prompt,
                tokens=len(request.prompt.split()),
                model="gemini-2.0-flash",
                created_at=datetime.utcnow()
            )
            db.add(user_message_main)
            
            assistant_message_main = Message(
                id=assistant_message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=content if isinstance(content, str) else str(content),
                tokens=len(str(content).split()),
                model="gemini-2.0-flash",
                created_at=datetime.utcnow()
            )
            db.add(assistant_message_main)
            db.flush()  # Get IDs
        
        # ========== CACHE CONVERSATION & MESSAGES (FOR ALL REQUESTS) ==========
        conversation_cache = ConversationCache(
            id=conversation_id,
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            title=request.prompt[:50],  # First 50 chars as title
            conversation_hash=conversation_hash,
            message_count=1,
            total_tokens=0,
            platform="api",
            tone=request.safety_level,
            language="en",
            migration_version="1.0"
        )
        try:
            db.add(conversation_cache)
            db.flush()  # Get ID without committing
        except Exception as flush_error:
            from sqlalchemy.exc import SQLAlchemyError
            print(f"❌ Error flushing conversation_cache: {flush_error}")
            if isinstance(flush_error, SQLAlchemyError):
                print(f"SQL Error: {flush_error.orig}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise
        
        # Add user message to message_cache
        user_message = MessageCache(
            id=user_message_id,
            conversation_id=conversation_id,
            role="user",
            content=request.prompt,
            message_hash=hashlib.md5(request.prompt.encode()).hexdigest(),
            sequence=len(history),
            tokens=len(request.prompt.split()),  # Rough estimate
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        
        # Add assistant message to message_cache
        assistant_message = MessageCache(
            id=assistant_message_id,
            conversation_id=conversation_id,
            role="assistant",
            content=content if isinstance(content, str) else str(content),
            message_hash=hashlib.md5((content if isinstance(content, str) else str(content)).encode()).hexdigest(),
            sequence=len(history) + 1,
            tokens=len(str(content).split()),  # Rough estimate
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        
        # ========== STEP 7: STORE IN PROMPT CACHE (DEDUPLICATION) ==========
        # ========== STEP 7: STORE IN PROMPT CACHE (DEDUPLICATION) ==========
        content_str = content if isinstance(content, str) else str(content)
        response_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        prompt_cache_entry = PromptCache(
            id=str(uuid.uuid4()),
            prompt_hash=prompt_hash,
            prompt_text=request.prompt,
            response_text=content_str,
            response_hash=response_hash,
            model="gemini-2.0-flash",
            hits=1,  # First hit
            generation_time=int((time.time() - start_time) * 1000),
            created_at=datetime.utcnow()
        )
        db.add(prompt_cache_entry)
        
        # ========== STEP 8A: CALCULATE QUALITY SCORES ==========
        
        seo_score = calculate_seo_score(content_str)
        uniqueness_score = calculate_uniqueness_score(content_str, request.prompt)
        engagement_score = calculate_engagement_score(content_str)
        
        # ========== STEP 8B: GENERATE EMBEDDING ==========
        embedding_vector = generate_embedding(content_str)
        
        # ========== STEP 8C: CALCULATE COST ==========
        input_tokens = len(request.prompt.split())
        output_tokens = len(content_str.split())
        request_cost = calculate_cost("gemini-2.0-flash", input_tokens, output_tokens)
        
        # ========== STEP 8D: STORE IN GENERATED_CONTENT (MAIN TABLE - FOR ALL USERS) ==========
        generated_content_id = None
        # Store for both authenticated and API/guest users
        generated_content = GeneratedContent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=None,  # No conversation context for API requests
            message_id=None,
            original_prompt=request.prompt,
            requirements={"safety_level": request.safety_level},
            content_type="text",
            platform="api",
            generated_content={
                "text": content_str,
                "model": "gemini-2.0-flash",
                "timestamp": datetime.utcnow().isoformat()
            },
            # ✅ NOW INCLUDE QUALITY SCORES
            seo_score=seo_score,
            uniqueness_score=uniqueness_score,
            engagement_score=engagement_score,
            status="generated",
            created_at=datetime.utcnow()
        )
        db.add(generated_content)
        db.flush()  # Get ID
        generated_content_id = generated_content.id
        
        # Only create embeddings for authenticated users
        if user_id is not None:
            content_embedding = ContentEmbedding(
                id=str(uuid.uuid4()),
                content_id=generated_content_id,
                text_source="generated_content",
                source_id=generated_content_id,
                embedded_text=content_str[:500],  # First 500 chars for reference
                text_length=len(content_str),
                text_tokens=output_tokens,
                embedding=embedding_vector,  # Vector already a list
                embedding_model="all-MiniLM-L6-v2",
                embedding_dimensions=384,
                confidence_score=1.0,
                is_valid=True,
                created_at=datetime.utcnow()
            )
            db.add(content_embedding)
            
            # ========== STEP 9: LINK IN CACHE_CONTENT_MAPPING ==========
            mapping = CacheContentMapping(
                id=str(uuid.uuid4()),
                cache_type="prompt",
                cache_id=prompt_cache_entry.id,
                content_id=generated_content_id,
                user_id=user_id,
                cache_backend="postgresql",
                content_backend="postgresql",
                is_synced=True,
                last_synced_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(mapping)
            
            # ========== STEP 10: UPDATE USAGE & CACHE METRICS (ONLY FOR AUTHENTICATED USERS) ==========
            user_metrics = get_or_create_usage_metrics(db, user_id, tier="free" if not is_premium else "premium")
            if user_metrics:
                user_metrics.total_requests += 1
                user_metrics.cache_misses += 1
                user_metrics.monthly_requests_used += 1
                user_metrics.total_input_tokens += input_tokens
                user_metrics.total_output_tokens += output_tokens
                user_metrics.total_tokens += input_tokens + output_tokens
                
                # ✅ ADD COST TRACKING
                user_metrics.total_cost += request_cost
                user_metrics.cache_cost += 0  # No cache cost for generated content
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                if user_metrics.total_requests > 0:
                    user_metrics.average_response_time_ms = (
                        (user_metrics.average_response_time_ms * (user_metrics.total_requests - 1) + elapsed_ms) 
                        / user_metrics.total_requests
                    )
                    user_metrics.cache_hit_rate = user_metrics.cache_hits / user_metrics.total_requests
            else:
                # For guest requests, only track elapsed time
                elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Update cache metrics (for all requests)
        cache_metrics = get_or_create_cache_metrics(db)
        cache_metrics.total_entries += 1
        cache_metrics.cache_misses += 1
        
        # Commit all changes
        db.commit()
        
        return GenerateContentResponse(
            success=True,
            content=content_str,
            safety_checks=safety_report,
            tokens_used=output_tokens,
            rate_limit_remaining=remaining,
            rate_limit_reset_after=0,
            cached=False,
            cache_hit_rate=user_metrics.cache_hit_rate if user_metrics else 0.0,
            generation_time_ms=elapsed_ms,
            # ✅ Include quality scores
            seo_score=seo_score,
            uniqueness_score=uniqueness_score,
            engagement_score=engagement_score,
            # ✅ Include cost
            cost_usd=request_cost,
            total_cost_usd=user_metrics.total_cost if user_metrics else 0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        db.rollback()
        error_details = traceback.format_exc()
        print(f"🔴 Content generation error: {str(e)}")
        print(f"Traceback:\n{error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check if content generation service is available."""
    try:
        config = AgentConfig()
        agent = get_agent(config)
        
        # Test with simple prompt
        response = agent.invoke(
            user_message="Hello",
            conversation_history=[]
        )
        
        return {
            "status": "ok",
            "model": "gemini-2.0-flash",
            "platform": "Vertex AI",
            "test_response": response[:50] + "..." if len(response) > 50 else response,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )


@router.get("/models")
async def list_models():
    """List available Vertex AI models."""
    return {
        "models": [
            {
                "name": "gemini-2.0-flash",
                "description": "Latest fast Gemini model",
                "context_window": 100000,
            },
            {
                "name": "gemini-1.5-pro",
                "description": "High-capability Gemini model",
                "context_window": 1000000,
            },
            {
                "name": "gemini-1.5-flash",
                "description": "Fast Gemini model",
                "context_window": 1000000,
            },
        ]
    }
