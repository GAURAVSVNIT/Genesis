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
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import re

from graph.content_agent import create_agent
from core.config import settings
from core.rate_limiter import RATE_LIMITERS
from core.upstash_redis import RedisManager
from core.response_cache import CACHES
from database.database import SessionLocal
from database.models.cache import (
    ConversationCache,
    MessageCache,
    PromptCache,
    CacheMetrics,
    CacheEmbedding,
)
from database.models.content import (
    GeneratedContent,
    UsageMetrics,
    ContentEmbedding,
)
from database.models.conversation import Conversation, Message


def get_db():
    """Get database session."""
    db = None
    try:
        if SessionLocal:
             db = SessionLocal()
    except Exception as e:
        print(f"Database connection error: {e}")
        # db remains None
    
    try:
        yield db
    finally:
        try:
            if db:
                db.close()
        except:
            pass

def safe_debug_log(message: str, filename: str = "debug_redis.log"):
    """Safely write debug logs without crashing on file errors."""
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        # Silently fail - debug logging shouldn't crash the API
        pass


# ========== SEO OPTIMIZATION ==========
from intelligence.seo.optimizer import optimize_content
from intelligence.seo.config import SEOConfig

# Helper to extract keywords from prompt (simple version)
def extract_keywords_from_prompt(prompt: str) -> List[str]:
    """Extract potential keywords from prompt."""
    # Remove common stop words and return top 3 longest words
    stop_words = {'write', 'about', 'create', 'generate', 'blog', 'post', 'article', 'the', 'and', 'for', 'with'}
    words = [w.lower() for w in re.findall(r'\b\w+\b', prompt) if w.lower() not in stop_words]
    # Sort by length descending
    words.sort(key=len, reverse=True)
    return words[:3]


def _infer_tone_from_content(content: str) -> str:
    """
    Infer tone from content using simple keyword and pattern analysis.
    Returns one of: professional, casual, technical, educational, inspirational, neutral
    """
    content_lower = content.lower()
    
    # Technical indicators
    technical_keywords = ['algorithm', 'implementation', 'architecture', 'api', 'framework', 
                          'protocol', 'system', 'code', 'function', 'class', 'method']
    technical_score = sum(1 for word in technical_keywords if word in content_lower)
    
    # Casual indicators
    casual_patterns = ['!', '?', 'hey', 'wow', 'awesome', 'cool', 'check out', 'guess what']
    casual_score = sum(1 for pattern in casual_patterns if pattern in content_lower)
    
    # Professional indicators
    professional_keywords = ['enterprise', 'strategy', 'business', 'management', 'corporate',
                            'industry', 'professional', 'stakeholder', 'analytics']
    professional_score = sum(1 for word in professional_keywords if word in content_lower)
    
    # Educational indicators
    educational_keywords = ['learn', 'tutorial', 'guide', 'how to', 'step by step', 
                           'beginners', 'understand', 'explain', 'introduction']
    educational_score = sum(1 for word in educational_keywords if word in content_lower)
    
    # Inspirational indicators
    inspirational_keywords = ['inspire', 'motivate', 'achieve', 'success', 'growth',
                             'transform', 'empower', 'journey', 'breakthrough']
    inspirational_score = sum(1 for word in inspirational_keywords if word in content_lower)
    
    # Determine highest score
    scores = {
        'technical': technical_score,
        'casual': casual_score,
        'professional': professional_score,
        'educational': educational_score,
        'inspirational': inspirational_score
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return 'neutral'
    
    return max(scores, key=scores.get)


def _enhance_prompt_with_preferences(
    base_query: str,
    style_preference: Optional[str],
    exclude_elements: Optional[List[str]],
    variation_level: Optional[str]
) -> str:
    """
    Enhance the generated prompt with user preferences.
    """
    enhanced = base_query
    
    # Add style preference
    if style_preference:
        style_map = {
            'photorealistic': 'Photorealistic style, high detail, professional photography quality',
            'illustration': 'Digital illustration style, artistic, vibrant colors',
            '3d_render': '3D rendered style, modern, clean design, ray-traced lighting',
            'minimalist': 'Minimalist design, clean lines, simple composition, negative space',
            'cinematic': 'Cinematic style, dramatic lighting, film-like quality, atmospheric'
        }
        if style_preference in style_map:
            enhanced = f"{enhanced}. Style: {style_map[style_preference]}"
        else:
            enhanced = f"{enhanced}. Style: {style_preference}"
    
    # Add exclusions
    if exclude_elements:
        exclusions = ', '.join(exclude_elements)
        enhanced = f"{enhanced}. Avoid including: {exclusions}"
    
    # Add variation instructions based on level
    if variation_level:
        variation_map = {
            'low': 'Maintain consistent style and composition',
            'medium': 'Explore creative variations while keeping core theme',
            'high': 'Bold creative interpretation, unique perspective'
        }
        if variation_level in variation_map:
            enhanced = f"{enhanced}. {variation_map[variation_level]}"
    
    return enhanced


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
    "gemini-2.5-flash": {
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
    pricing = PRICING.get(model, PRICING["gemini-2.5-flash"])
    
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
    intent: str = "chat" # 'chat', 'blog', 'edit', 'rewrite', 'image'
    conversation_history: Optional[List[Message]] = None
    safety_level: str = "moderate"  # 'strict', 'moderate', 'permissive'
    guestId: Optional[str] = None
    tone: str = "analytical"  # 'analytical', 'opinionated', 'critical', 'investigative', 'contrarian'
    include_critique: bool = True  # Include critical analysis
    include_alternatives: bool = True  # Include alternative perspectives
    include_implications: bool = True  # Include real-world implications
    format: str = "markdown"  # 'markdown', 'html', 'plain', 'structured'

    max_words: Optional[int] = None  # Maximum word count
    include_sections: bool = True  # Include section breaks
    model: str = "gemini-2.5-flash"  # Model selection - defaults to Gemini, can be changed to gpt-4o-mini, etc.


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
    # Quality Scores (0-1)
    seo_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    engagement_score: Optional[float] = None
    # Cost Tracking
    cost_usd: Optional[float] = None
    total_cost_usd: Optional[float] = None
    # Rich Data for Frontend
    seo_data: Optional[dict] = None
    trend_data: Optional[dict] = None
    image_url: Optional[str] = None
    model: Optional[str] = None
    image_model: Optional[str] = None
    # Tone and Style Info
    tone_applied: str = "analytical"
    includes_critique: bool = True
    includes_alternatives: bool = True
    includes_implications: bool = True
    analysis_depth: str = "comprehensive"
    # Formatting Info
    format_applied: str = "markdown"
    word_count: int = 0
    sections_count: int = 0


class AgentConfig(BaseModel):
    """Configuration for the agent."""
    gcp_project_id: Optional[str] = None
    model: str = "gemini-2.5-flash"
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
    """
    import time
    start_time = time.time()
    
    import time
    start_time = time.time()
    
    try:
        # Import required modules at function level
        from intelligence.seo.optimizer import SEOOptimizer, optimize_content
        from intelligence.seo.config import SEOConfig
        
        # ========== INITIALIZATION ==========
        # Check database connection first
        if not db:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please try again later."
            )
        
        user_metrics = None  # Initialize for all paths
        elapsed_ms = 0
        
        user_metrics = None  # Initialize for all paths
        elapsed_ms = 0
        
        # ========== STEP 1: RATE LIMITING ==========
        relevant_image_url = None # Initialize variable
        # Use guestId if provided (guest user), otherwise guest identifier
        guest_id = request.guestId
        safe_debug_log(f"[DEBUG] Initial guest_id from request: {guest_id}, prompt len: {len(request.prompt)}\n")
        
        # Determine identifier for rate limiting
        if guest_id:
            identifier = guest_id
            # cache_user_id can be guest_id for redis/cache tracking
            cache_user_id = guest_id
            # auth_user_id must be None for guests (unless we verify it's a real user, which we assume not if passed as guestId)
            auth_user_id = None
        else:
            client_ip = http_request.client.host if http_request.client else "unknown"
            identifier = client_ip
            cache_user_id = None
            auth_user_id = None
        
        # Override if authenticated user logic exists (omitted here as we rely on explicit user_id handling in backend flow usually)
        # But for this file, user_id seems to come from request params or auth middleware not fully shown.
        # Assuming guest flow:
        user_id = auth_user_id 
        
        is_premium = False
        
        client_ip = http_request.client.host if http_request.client else "unknown"
        
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
            .filter_by(prompt_hash=prompt_hash, model=request.model)\
            .first()

        # ... (keep existing cache hit logic) ...

        if cached_prompt:
            # ✅ CACHE HIT! Store in generated_content for tracking
            cached_prompt.hits += 1
            
            # [NEW] Run lightweight analysis to populate metadata for cached content
            from intelligence.trend_collector import TrendCollector
            from intelligence.trend_analyzer import TrendAnalyzer
            
            # Extract keywords (needed for trends and image)
            keywords = extract_keywords_from_prompt(request.prompt)
            
            # Analyze Trends
            trend_collector = TrendCollector(use_cache=True)
            trend_analyzer = TrendAnalyzer()
            
            # Await trend collection
            print(f" [Trends] Collecting trends for cached content...")
            trend_data = await trend_collector.collect_all_trends(keywords)
            trend_analysis = await trend_analyzer.analyze_for_generation(request.prompt, keywords, trend_data)
            
            # Construct trend context
            trend_context = ""
            if trend_analysis.get("trending_topics"):
                top_trends = [t.get("title", "") for t in trend_analysis["trending_topics"][:3]]
                trend_context = f"\n\nTrending Context: The following topics are currently trending and relevant to this request: {', '.join(top_trends)}. Incorporate these angles where appropriate."

            # Analyze SEO (on cached content) using the selected model
            seo_config = SEOConfig(model_name=request.model)
            seo_result = await optimize_content(
                content=cached_prompt.response_text,
                keywords=keywords,
                platform="blog",
                context=trend_context, 
                config=seo_config
            )
            
            # Merge Trend Recommendations into SEO result
            if trend_analysis.get("recommendations"):
                 if "suggestions" not in seo_result:
                     seo_result["suggestions"] = []
                 seo_result["suggestions"].extend(trend_analysis["recommendations"][:3])
                 
            seo_result["trend_data"] = trend_analysis
            
            # Calculate Scores
            seo_score = seo_result.get("seo_score", 0.0) / 100.0
            uniqueness_score = 0.8
            engagement_score = 0.8

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
                    "model": cached_prompt.model,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "cache",
                    "seo_data": seo_result
                },
                seo_score=seo_score,
                uniqueness_score=uniqueness_score,
                engagement_score=engagement_score,
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
            
            # Generate Image on Cache Hit to ensure consistent experience
            image_url = None
            try:
                from intelligence.image_collector import ImageCollector
                image_collector = ImageCollector()
                
                # Image search query from keywords already extracted
                image_search_query = keywords[0] if keywords else request.prompt[:20]
                
                # Fetch image
                print(f" [Cache Hit] Fetching image for: {image_search_query} with OpenAI DALL-E")
                image_url = await image_collector.get_relevant_image(image_search_query, model_provider="gpt")
            except Exception as e:
                print(f"[Cache Hit] Image generation failed: {e}")
                
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
                generation_time_ms=elapsed_ms,
                image_url=image_url,
                model=cached_prompt.model if getattr(cached_prompt, 'model', None) else "cached-model",
                image_model="dall-e-3" if getattr(cached_prompt, 'model', None) and cached_prompt.model.startswith("gpt") else "vertex-imagen",
                # Add defaulting for missing fields on cache hit
                seo_score=0.0,
                uniqueness_score=0.0,
                trend_data=None,
                cost_usd=0.0,
                engagement_score=0.0
            )
        
        # ========== STEP 4: GENERATE NEW CONTENT (CACHE MISS) ==========
        # Import tone enhancer
        from intelligence.tone_enhancer import (
            get_enhanced_system_prompt, 
            get_content_enrichment_prompt, 
            get_opinion_enrichment_prompt,
            get_formatted_output_prompt
        )
        
        # Create agent with selected model
        agent = create_agent(
            gcp_project_id=settings.GCP_PROJECT_ID,
            model=request.model,
            safety_level=request.safety_level
        )
        
        # Convert conversation history
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=msg.content))
        
        # ========== STEP 3.5: EXTRACT KEYWORDS & ANALYZE TRENDS (MOVED UP FOR CONTEXT SYNC) ==========
        # Extract keywords early for trend analysis
        
        # Use the selected model for SEO optimization (respects user's model choice)
        try:
            seo_optimizer = SEOOptimizer(config=SEOConfig(model_name=request.model))
            keywords = await seo_optimizer.extract_keywords(request.prompt)
            print(f" [SEO] Extracted keywords using {request.model}: {keywords}")
        except Exception as e:
            print(f" [SEO] Keyword extraction failed with {request.model}, using simple fallback: {e}")
            # Simple fallback - extract words from prompt
            keywords = [word.lower() for word in request.prompt.split() if len(word) > 3][:5]
            print(f" [SEO] Fallback keywords: {keywords}")

        # Initialize trend services
        from intelligence.trend_collector import TrendCollector
        from intelligence.trend_analyzer import TrendAnalyzer
        from intelligence.image_collector import ImageCollector
        
        trend_collector = TrendCollector(use_cache=True)
        trend_analyzer = TrendAnalyzer()
        image_collector = ImageCollector()
        
        # Fetch and analyze trends
        print(f" [Trends] Starting trend collection for keywords: {keywords}")
        trend_data = await trend_collector.collect_all_trends(keywords)
        
        print(f" [Trends] Analyzing trends for relevance to content...")
        trend_analysis = await trend_analyzer.analyze_for_generation(request.prompt, keywords, trend_data)
        
        # Extract trend insights to enrich the prompt
        trend_context = ""
        if trend_analysis.get("trending_topics"):
            top_trends = [t.get("title", "") for t in trend_analysis["trending_topics"][:3]]
            formatted_trends = ", ".join(top_trends)
            trend_context = f"\n\nCONTEXT FROM CURRENT TRENDS:\nThe following related topics are currently trending and should be subtly reflected in the content where relevant: {formatted_trends}."
            if trend_analysis.get("recommendations"):
                 recs = "; ".join(trend_analysis["recommendations"][:2])
                 trend_context += f"\nSpecific Trend Insights: {recs}"

        # Build enhanced prompt with tone and style instructions
        enhanced_system_prompt = get_enhanced_system_prompt(
            base_topic=request.prompt,
            tone=request.tone,
            add_critical_thinking=request.include_critique,
            include_multiple_perspectives=request.include_alternatives
        ) + trend_context

        
        # Add enrichment instructions
        enrichment_instruction = ""
        if request.include_critique or request.include_alternatives or request.include_implications:
            enrichment_instruction = "\n\n" + get_content_enrichment_prompt()
        
        # Add formatting instructions
        formatting_instruction = "\n\n" + get_formatted_output_prompt(
            format_type=request.format,
            max_words=request.max_words,
            include_sections=request.include_sections,
            tone=request.tone
        )
        
        # Combine with enhanced system prompt
        enhanced_prompt = enhanced_system_prompt + enrichment_instruction + formatting_instruction
        
        # Add to conversation history as a system message
        if history:
            # If there's history, prepend the enhanced system message
            history = [SystemMessage(content=enhanced_prompt)] + history
        
        print(f"[MODEL INFO] GenerateContentRequest - Model: {request.model}, Intent: {request.intent}, Prompt: {request.prompt[:50]}...")
        
        # Check cache early
        # Generate cache key based on prompt and parameters
        
        # If no history, we must pass the enhanced prompt as the user message for it to take effect
        # Otherwise it's just a system message that might be ignored by some agent implementations if not passed correctly
        final_user_message = request.prompt
        if not history:
             # If no history, wrap the prompt with system instructions as the input
             # or better, just pass the enhanced prompt as the user message for this turn
             final_user_message = enhanced_prompt
        
        content = agent.invoke(
            user_message=final_user_message,
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
        if user_id is not None and len(str(user_id)) == 36:  # Only if authenticated with valid UUID
            real_conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=request.prompt[:100],  # First 100 chars as title
                description=None,
                agent_type="text-generation",
                model_used=request.model,
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
                model=request.model,
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
                model=request.model,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message_main)
            db.flush()  # Get IDs
        

        # ========== CACHE CONVERSATION & MESSAGES (FOR ALL REQUESTS) ==========
        # LOGIC: Try to append to existing conversation if it exists (unified history), otherwise create new.
        
        # Determine effective user_id/guest_id for query
        query_user_id = user_id if user_id else cache_user_id
        is_guest_mode = (query_user_id == cache_user_id) # True if we are using guest_id not authenticated user_id
        
        existing_conversation = None
        if query_user_id:
             # Try to find existing conversation to append to
             # For guests, guest.py uses platform="guest"
             # For authenticated users, platform="api" vs "chat" might differ, but let's try to unify.
             existing_conversation = db.query(ConversationCache).filter_by(
                user_id=query_user_id,
                platform="guest" if is_guest_mode else "api" 
            ).first()
        
        if existing_conversation:
             # REUSE EXISTING
             conversation_id = existing_conversation.id
             # Increment message count (User + AI = +2)
             existing_conversation.message_count += 2
             existing_conversation.updated_at = datetime.utcnow()
             existing_conversation.accessed_at = datetime.utcnow()
             db.add(existing_conversation) # Mark for update
             # Use existing sequence count for next messages
             current_sequence = existing_conversation.message_count - 1 # approximate, strict sequence managed by DB usually or append
        else:
            # CREATE NEW
             conversation_cache = ConversationCache(
                id=conversation_id,
                user_id=query_user_id, # Use auth ID if available, else guest ID
                session_id=str(uuid.uuid4()) if not guest_id else guest_id,
                title=request.prompt[:50],  # First 50 chars as title
                conversation_hash=conversation_hash,
                message_count=2, # Initial (User + AI)
                total_tokens=0,
                platform="guest" if is_guest_mode else "api", # Use 'guest' platform if guest to match guest.py
                tone=request.safety_level,
                language="en",
                migration_version="1.0"
            )
             try:
                db.add(conversation_cache)
                db.flush()  # Get ID without committing
             except Exception as flush_error:
                print(f" Error flushing conversation_cache: {flush_error}")
                # Fallback to just logging error but continuing if possible (or raise)
                raise
        
        # Add messages to message_cache (FOR ALL USERS)
        if True:  # Changed from checking user_id to allow all
            # Add user message to message_cache
            user_message = MessageCache(
                id=user_message_id,
                conversation_id=conversation_id,
                role="user",
                content=request.prompt,
                message_hash=hashlib.md5(request.prompt.encode()).hexdigest(),
                sequence=existing_conversation.message_count - 1 if existing_conversation else 1, # Sequence logic
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
                sequence=existing_conversation.message_count if existing_conversation else 2,
                tokens=len(str(content).split()),  # Rough estimate
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
        

        # ========== STEP 7: STORE IN PROMPT CACHE (DEDUPLICATION) ==========
        content_str = content if isinstance(content, str) else str(content)
        response_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        prompt_cache_entry = PromptCache(
            id=str(uuid.uuid4()),
            prompt_hash=prompt_hash,
            prompt_text=request.prompt,
            response_text=content_str,
            response_hash=response_hash,
            model=request.model,
            hits=1,  # First hit
            generation_time=int((time.time() - start_time) * 1000),
            created_at=datetime.utcnow()
        )
        try:
            db.add(prompt_cache_entry)
            db.commit()
        except Exception as e:
            # Handle race condition where another request cached this prompt simultaneously
            print(f"[Cache] Race condition or error caching prompt: {e}")
            db.rollback()
            # Continue without failing the request

        
        # ========== STEP 7.5: STORE IN REDIS (HOT CACHE FOR GUESTS) ==========
        # Store in Redis for guest sessions (consistent with api/v1/guest.py)
        safe_debug_log(f"\n[{datetime.utcnow().isoformat()}] Processing Request for Guest: {guest_id}\n")
            
        if guest_id:
            try:
                redis = RedisManager.get_instance()
                if not redis:
                     safe_debug_log(f"[ERROR] RedisManager returned None!\n")
                else:
                    key = f"guest:{guest_id}"
                    safe_debug_log(f"[INFO] Using Redis Key: {key}\n")
                    
                    # 1. Store User Prompt
                    user_msg_redis = {
                        "role": "user",
                        "content": request.prompt,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    res1 = redis.rpush(key, json.dumps(user_msg_redis))
                    safe_debug_log(f"[INFO] rpush user result: {res1}\n")
                    
                    # 2. Store AI Response
                    ai_msg_redis = {
                        "role": "assistant",
                        "content": content_str,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    res2 = redis.rpush(key, json.dumps(ai_msg_redis))
                    safe_debug_log(f"[INFO] rpush ai result: {res2}\n")
                    
                    # Set expiration (24 hours)
                    redis.expire(key, 86400)
                    safe_debug_log(f"[INFO] Expiration set\n")
                
            except Exception as e:
                safe_debug_log(f"[ERROR] Exception: {str(e)}\n")
                import traceback
                safe_debug_log(traceback.format_exc() + "\n")
        else:
             safe_debug_log(f"[WARN] No guest_id provided, skipping Redis cache\n")
        
          # ========== STEP 8A: SEO OPTIMIZATION (POST-GENERATION) ==========
        # (Keywords extracted earlier at Step 3.5)
        
        # Optimize the generated content
        print(f" [SEO] optimizing generated content...")
        seo_result = await seo_optimizer.optimize_content(
             content=content_str,
             target_keyword=keywords[0] if keywords else request.prompt[:20]
        )
        
        # Calculate SEO Score (0-100 normalized to 0-1)
        seo_score = min(max(seo_result.get("seo_score", 50) / 100.0, 0.0), 1.0)
        uniqueness_score = 0.85 # Placeholder until integrated
        engagement_score = 0.8 # Placeholder until integrated
        
        # ========== STEP 8C: IMAGE GENERATION ==========
        # Use AI Art Director for enhanced prompt
        from intelligence.image_prompter import generate_image_prompt
        
        relevant_image_url = None
        
        # Check intent for image generation
        should_generate_image = request.intent in ['blog', 'rewrite', 'image']
        
        if should_generate_image:
            try:
                print(f" [Image] Consulting Art Director for: {request.prompt[:30]}... (Tone: {request.tone})")
                
                # Determine context source based on intent
                summary_context = None
                if request.intent in ['blog', 'rewrite']:
                    # For blogs, use the generated content as context
                    summary_context = content_str[:1000] if content_str else None
                
                # Generate enhanced prompt
                image_query = await generate_image_prompt(
                    topic=request.prompt, 
                    keywords=keywords, 
                    tone=request.tone, 
                    summary=summary_context,
                    trends=top_trends if 'top_trends' in locals() else None,
                    model=request.model  # Use the same model as content generation
                )
                print(f" [Image] Generative Query (using {request.model}): {image_query[:50]}...")
                
                # Fetch image using enhanced query with OpenAI
                relevant_image_url = await image_collector.get_relevant_image(image_query, model_provider="gpt")
                
                if relevant_image_url:
                     print(f" [Image] Generated successfully.")
                else:
                     print(f" [Image] Failed to generate.")
                     
            except Exception as e:
                print(f" [Image] Generation failed: {e}")
                relevant_image_url = None
        else:
            print(f" [Image] Skipping generation for intent: {request.intent}")
        # I will RESTORE/KEEP it but ensure it's reliable and logs well.
        
        # Re-reading user request: "add a node for it ... or make it async like text comes and image generates"
        # Since I am in the API, "text comes" means separate streams or endpoints. 
        # Current API is one-shot.
        # So "node for it" in the synchronous flow is best.
        
        # I will keep the explicit generation here (as I did in the cache hit) 
        # but ensure it uses the NEW 'image_agent' logic if I can, or just 'ImageCollector'.
        # 'ImageCollector' is the logic. 'image_agent.py' is just a wrapper for the graph.
        # So calling 'ImageCollector' here is correct for this imperative endpoint.
        
        # Fetch image based on primary keyword
        try:
            if not relevant_image_url: # Only if not already fetched
                 image_search_query = keywords[0] if keywords else request.prompt[:20]
                 print(f"[Images] Fetching image for: {image_search_query} with OpenAI DALL-E")
                 relevant_image_url = await image_collector.get_relevant_image(image_search_query, model_provider="gpt")
                 
                 # Retry with safer abstract prompt if failed
                 if not relevant_image_url:
                     print(f"[Images] Primary query failed. Retrying with abstract concept...")
                     safe_query = f"Abstract representation of {image_search_query}"
                     relevant_image_url = await image_collector.get_relevant_image(safe_query, model_provider="gpt")

                 if relevant_image_url:
                     print(f" [Images] Found image: {relevant_image_url}")
                 else:
                     print(f" [Images] No image found or API not configured.")
        except Exception as e:
            print(f"[Content] Image generation failed gracefully: {e}")
            relevant_image_url = None
        

        
        # Extract trend insights to enrich the prompt
        trend_context = ""
        if trend_analysis.get("trending_topics"):
            top_trends = [t.get("title", "") for t in trend_analysis["trending_topics"][:3]]
            trend_context = f"\n\nTrending Context: The following topics are currently trending and relevant to this request: {', '.join(top_trends)}. Incorporate these angles where appropriate."
            
            # Enrich the prompt for the actual generation if possible
            # Note: We've already generated the main content in Step 4. 
            # Ideally, this trend analysis should happen BEFORE Step 4 to influence the generation.
            # However, for now, we will use it to optimize the SEO metadata and suggestions.
            # If we want to influence the TEXT itself, we would need to move this block up or re-generate.
            # Given the flow, we will pass this context to the SEO Optimizer to refine the content.
        
        # Optimize content
        # We explicitly await this as it uses async AI calls
        # We pass the trend context to the optimizer config or prompt if supported
        seo_config = SEOConfig(model_name=request.model)
        # You might extend SEOConfig or the optimize_content prompt to accept "context"
        
        seo_result = await optimize_content(
            content=content_str, # Original content
            keywords=keywords,
            platform="blog", # Defaulting to blog for now
            context=trend_context, # Pass trend context for re-generation
            config=seo_config
        )
        
        # Inject trend recommendations into the SEO result
        if trend_analysis.get("recommendations"):
             if "suggestions" not in seo_result:
                 seo_result["suggestions"] = []
             seo_result["suggestions"].extend(trend_analysis["recommendations"][:3])
             
        # Store trend data in the result for frontend to display
        seo_result["trend_data"] = trend_analysis
        
        # Extract scores and data
        seo_score = seo_result.get("seo_score", 0.0) / 100.0 # Normalize to 0-1 for DB
        # Uniqueness and engagement can reuse the old logic or extraction if new model supports it.
        # For now, we'll keep uniqueness/engagement as placeholders or simple heuristics if needed,
        # but the new model focuses on SEO. We'll derive scores from the SEO result if possible.
        # Since the new optimizer doesn't output explicit "uniqueness" or "engagement" scores yet,
        # we can use the "overall_score" or just default 0.8 for now to avoid errors.
# ========== STEP 8B: GENERATE EMBEDDING ==========
        embedding_vector = generate_embedding(content_str)
        
        # ========== STEP 8C: CALCULATE UNIQUENESS ==========
        # Calculate uniqueness by comparing with recent embeddings
        # We define a helper here or call it from a utility
        
        import numpy as np
        
        def _calc_uniqueness(db_session, target_vector, limit=50):
            try:
                # Fetch recent embeddings
                recent = db_session.query(ContentEmbedding.embedding)\
                    .filter(ContentEmbedding.is_valid == True)\
                    .order_by(ContentEmbedding.created_at.desc())\
                    .limit(limit)\
                    .all()
                
                if not recent:
                    return 1.0
                
                # Convert to numpy
                vectors = np.array([r[0] for r in recent if r[0]])
                if len(vectors) == 0:
                    return 1.0
                    
                target = np.array(target_vector)
                
                # Cosine Similarity
                # sim = dot(a, b) / (norm(a) * norm(b))
                norm_target = np.linalg.norm(target)
                norm_vectors = np.linalg.norm(vectors, axis=1)
                
                # Handle zero vectors
                if norm_target == 0:
                    return 0.0
                
                # Avoid division by zero for others
                valid_indices = norm_vectors > 0
                if not np.any(valid_indices):
                    return 1.0
                    
                vectors = vectors[valid_indices]
                norm_vectors = norm_vectors[valid_indices]
                
                similarities = np.dot(vectors, target) / (norm_vectors * norm_target)
                max_similarity = np.max(similarities)
                
                # Uniqueness is inverse of max similarity
                # If similarity is 1.0 (duplicate), uniqueness is 0.0
                return float(1.0 - max_similarity)
                
            except Exception as e:
                print(f"⚠️ Uniqueness calculation error: {e}")
                return 0.8 # Fallback
        
        uniqueness_score = _calc_uniqueness(db, embedding_vector)
        # Clip to ensure valid range 0-1
        uniqueness_score = max(0.0, min(1.0, uniqueness_score))
        
        engagement_score = 0.8 # Placeholder until integrated
        
        # ========== STEP 8D: CALCULATE COST ==========
        input_tokens = len(request.prompt.split())
        output_tokens = len(content_str.split())
        
        # Calculate cost
        token_cost_input = 0
        token_cost_output = 0
        
        # Pricing (Approximate)
        if request.model.startswith("gpt-4"):
            token_cost_input = (input_tokens / 1000000) * 5.00
            token_cost_output = (output_tokens / 1000000) * 15.00
        elif request.model.startswith("gpt-3.5"):
            token_cost_input = (input_tokens / 1000000) * 0.50
            token_cost_output = (output_tokens / 1000000) * 1.50
        else:
            # Gemini defaults (estimated)
            token_cost_input = (input_tokens / 1000000) * 0.10
            token_cost_output = (output_tokens / 1000000) * 0.40

        # Add Image Cost
        image_cost = 0.0
        if relevant_image_url:
            if request.model.startswith("gpt"):
                image_cost = 0.040 # DALL-E 3 Standard
            else:
                image_cost = 0.020 # Vertex AI Imagen

        request_cost = token_cost_input + token_cost_output + image_cost
        
        # ========== STEP 8E: STORE IN GENERATED_CONTENT (MAIN TABLE - FOR ALL USERS) ==========
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
                "text": seo_result.get("optimized_content", content_str), # Use optimized version if available
                "model": request.model,
                "timestamp": datetime.utcnow().isoformat(),
                "seo_data": seo_result # Store full rich SEO data
            },
            # NOW INCLUDE QUALITY SCORES
            seo_score=seo_score,
            uniqueness_score=uniqueness_score,
            engagement_score=engagement_score,
            status="generated",
            created_at=datetime.utcnow()
        )
        db.add(generated_content)
        db.flush()  # Get ID
        generated_content_id = generated_content.id
        
        # Create embeddings for ALL users (Guests included)
        if True:
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
            
            # Additional: Store in cache_embeddings for Chat consistency (mirroring guest.py behavior)
            # We reuse the same embedding vector generated for the content
            cache_embedding = CacheEmbedding(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                embedding=json.dumps(embedding_vector),  # cache_embeddings expects Text (JSON)
                embedding_model="all-MiniLM-L6-v2",     # Matches the model used in this file
                embedding_dim=len(embedding_vector),
                text_chunk=content_str[:1000] if content_str else "",
                chunk_index=0,
                migration_version="1.0",
                created_at=datetime.utcnow()
            )
            db.add(cache_embedding)
            
            # ========== STEP 9: UPDATE USAGE & CACHE METRICS (ONLY FOR AUTHENTICATED USERS WITH VALID ID) ==========
            if user_id is not None:
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
        
        # Calculate word count and section count
        word_count = len(content_str.split())
        section_count = len(re.findall(r'^#{1,3}\s+', content_str, re.MULTILINE)) if request.format == 'markdown' else 0
        
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
            #  Include quality scores
            seo_score=seo_score, # Normalized 0-1
            uniqueness_score=uniqueness_score, # Placeholder
            engagement_score=engagement_score, # Placeholder
            #  Include cost
            cost_usd=request_cost,
            total_cost_usd=user_metrics.total_cost if user_metrics else 0.0,
            #  Include rich data
            seo_data=seo_result,
            trend_data=trend_analysis,
            image_url=relevant_image_url,
            model=request.model,
            image_model="dall-e-3" if request.model.startswith("gpt") else "vertex-imagen",
            #  Include tone and analysis info
            tone_applied=request.tone,
            includes_critique=request.include_critique,
            includes_alternatives=request.include_alternatives,
            includes_implications=request.include_implications,
            analysis_depth="comprehensive" if any([request.include_critique, request.include_alternatives, request.include_implications]) else "standard",
            #  Include formatting info
            format_applied=request.format,
            word_count=word_count,
            sections_count=section_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        if db:
            try:
                db.rollback()
            except:
                pass
        error_details = traceback.format_exc()
        print(f" Content generation error: {str(e)}")
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
            "model": "gemini-2.5-flash",
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
                "name": "gemini-2.5-flash",
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


# Import ImageCollector
from intelligence.image_collector import ImageCollector

class RegenerateImageRequest(BaseModel):
    content: str
    tone: Optional[str] = None  # "professional", "casual", "technical", etc. - inferred if not provided
    style_preference: Optional[str] = None  # "photorealistic", "illustration", "3d_render", "minimalist", "cinematic"
    specific_focus: Optional[str] = None  # What to emphasize in the image
    exclude_elements: Optional[List[str]] = None  # Elements to avoid
    variation_level: Optional[str] = "medium"  # "low", "medium", "high" - controls creativity

class RegenerateImageResponse(BaseModel):
    image_url: Optional[str] = None

@router.post("/regenerate-image", response_model=RegenerateImageResponse)
async def regenerate_image(request: RegenerateImageRequest):
    """
    Regenerate an image based on the provided content (blog post) with enhanced customization.
    
    Supports:
    - Automatic tone inference from content
    - Style preferences (photorealistic, illustration, etc.)
    - Specific visual focus
    - Element exclusion
    - Variation control
    """
    try:
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="Content is required for image generation.")

        # Extract keywords with better logic - prioritize title/first paragraph
        content_lines = request.content.strip().split('\n')
        title_text = content_lines[0] if content_lines else ""
        first_para = ' '.join(content_lines[1:3]) if len(content_lines) > 1 else ""
        
        # Extract keywords from title and first paragraph (more relevant than full content)
        keywords_from_title = extract_keywords_from_prompt(title_text)
        keywords_from_content = extract_keywords_from_prompt(first_para or request.content[:500])
        keywords = list(dict.fromkeys(keywords_from_title + keywords_from_content))[:5]  # Top 5 unique
        
        # Infer tone if not provided
        tone = request.tone
        if not tone:
            tone = _infer_tone_from_content(request.content)
            print(f"[DEBUG] Inferred tone: {tone}")
        
        # Use AI Art Director for enhanced prompt
        from intelligence.image_prompter import generate_image_prompt
        
        # Create a smart summary - use first 3 paragraphs or 800 chars
        paragraphs = [p.strip() for p in request.content.split('\n\n') if p.strip()]
        smart_summary = ' '.join(paragraphs[:3])[:800] if paragraphs else request.content[:800]
        
        # Build enhanced topic with focus
        topic = title_text if title_text else smart_summary[:200]
        if request.specific_focus:
            topic = f"{topic} (Focus: {request.specific_focus})"
        
        print(f"[DEBUG] Regenerate Image Request")
        print(f"[DEBUG] - Tone: {tone}")
        print(f"[DEBUG] - Keywords: {keywords}")
        if request.style_preference:
            print(f"[DEBUG] - Style: {request.style_preference}")
        if request.exclude_elements:
            print(f"[DEBUG] - Excluding: {request.exclude_elements}")
        print(f"[DEBUG] Consulting Art Director...")
        
        # Generate the image prompt
        query = await generate_image_prompt(
            topic=topic,
            keywords=keywords,
            tone=tone,
            summary=smart_summary
        )
        
        # Enhance query with user preferences
        enhanced_query = _enhance_prompt_with_preferences(
            query,
            request.style_preference,
            request.exclude_elements,
            request.variation_level
        )
        
        print(f"[DEBUG] Enhanced Query: {enhanced_query[:100]}...")
        
        collector = ImageCollector()
        print(f"[DEBUG] ImageCollector initialized. Using OpenAI DALL-E")
        
        image_url = await collector.get_relevant_image(enhanced_query, model_provider="gpt")
        
        if not image_url:
             print("[ERROR] No image returned (Safety Block?)")
             raise HTTPException(status_code=422, detail="Image generation blocked by safety filters or returned no result.")

        return RegenerateImageResponse(image_url=image_url)

    except ValueError as ve:
         # Captured from ImageCollector
         print(f"[ERROR] Logic Error: {ve}")
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] Image regeneration error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Generation Error: {str(e)}")
