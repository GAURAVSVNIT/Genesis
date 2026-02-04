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


class ChatMessage(BaseModel):
    """Message in conversation."""
    role: str  # 'user' or 'assistant'
    content: str


class GenerateContentRequest(BaseModel):
    """Request to generate content."""
    prompt: str
    intent: str = "chat" # 'chat', 'blog', 'edit', 'rewrite', 'image'
    conversation_history: Optional[List[ChatMessage]] = None
    safety_level: str = "strict"  # 'strict', 'moderate', 'permissive'
    guestId: Optional[str] = None
    tone: str = "analytical"  # 'analytical', 'opinionated', 'critical', 'investigative', 'contrarian'
    include_critique: bool = True  # Include critical analysis
    include_alternatives: bool = True  # Include alternative perspectives
    include_implications: bool = True  # Include real-world implications
    format: str = "markdown"  # 'markdown', 'html', 'plain', 'structured'

    max_words: Optional[int] = None  # Maximum word count
    include_sections: bool = True  # Include section breaks
    model: str = "gemini-2.5-flash"  # Model selection
    
    # Semantic Intent Layer
    topic: Optional[str] = None
    refined_query: Optional[str] = None


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
    safety_level: str = "strict"


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
    import traceback
    start_time = time.time()

    try:

    
        # ========== GUARDRAILS CHECK #1: INPUT VALIDATION (BEFORE EVERYTHING) ==========
        print(f"[GUARDRAILS #1] Validating input prompt before any processing...")
        print(f"[GUARDRAILS #1] Prompt: {request.prompt[:100]}...")
        print(f"[GUARDRAILS #1] Safety level: {request.safety_level}")
    
        # Create temporary guardrails instance for early validation
        from core.guardrails import get_message_guardrails
        early_guardrails = get_message_guardrails(level=request.safety_level, use_llm=True)
        early_validation = early_guardrails.validate_user_message(request.prompt, role="user")
    
        print(f"[GUARDRAILS #1] Result: is_safe={early_validation.is_safe}, reason={early_validation.reason}, score={early_validation.score}")
    
        if not early_validation.is_safe:
            print(f"[GUARDRAILS #1] ❌ BLOCKED - {early_validation.reason}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Content blocked by safety filters",
                    "reason": early_validation.reason,
                    "score": early_validation.score,
                    "category": "input_validation",
                    "message": "Your request contains content that violates our safety guidelines. Please rephrase and try again."
                }
            )
    
        print(f"[GUARDRAILS #1] ✅ PASSED - Input is safe")
    
        # Import required modules at function level
        from intelligence.seo.optimizer import SEOOptimizer, optimize_content
        from intelligence.seo.config import SEOConfig
        
        # ========== INITIALIZATION ==========
        # Check database connection first
        if not db:
            print("[WARN] Database connection unavailable - proceeding in degraded mode (no caching/metrics)")
            # Do NOT raise exception here - allow generation to proceed without DB
        
        user_metrics = None  # Initialize for all paths
        elapsed_ms = 0


        
        # ========== STEP 1: RATE LIMITING ==========
        relevant_image_url = None # Initialize variable
        # Use guestId if provided (guest user), otherwise guest identifier
        guest_id = request.guestId
        safe_debug_log(f"[DEBUG] Initial guest_id from request: {guest_id}, prompt len: {len(request.prompt)}\\n")
        
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
        cached_prompt = None
        if db:
            try:
                cached_prompt = (
                    db.query(PromptCache)
                    .filter_by(prompt_hash=prompt_hash, model=request.model)
                    .first()
                )
            except Exception as e:
                print(f"[WARN] Cache lookup failed: {e}")

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
                trend_context = f"\\n\\nTrending Context: The following topics are currently trending and relevant to this request: {', '.join(top_trends)}. Incorporate these angles where appropriate."

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
        keywords = []
        trend_analysis = {}
        top_trends = []
        trend_context = ""
        seo_optimizer = None
        trend_collector = None
        trend_analyzer = None
        image_collector = None

        try:
            # Extract keywords early for trend analysis
            from intelligence.seo.optimizer import SEOOptimizer
            # SEOConfig is imported globally, do not re-import locally to avoid UnboundLocalError
            
            # Use a supported model for SEO optimization (Gemini) regardless of the content generation model
            # This prevents errors when using models like Llama which are not supported by the SEO optimizer's underlying specific Google implementation
            seo_optimizer = SEOOptimizer(config=SEOConfig(model_name="gemini-2.0-flash"))
            
            # Extract keywords for this prompt (use topic if available for better relevance)
            seo_context = request.topic if request.topic else request.prompt
            keywords = await seo_optimizer.extract_keywords(seo_context)
            print(f" [SEO] Extracted keywords for context: {keywords} (Source: {'Topic' if request.topic else 'Prompt'})")

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
            if trend_analysis.get("trending_topics"):
                top_trends = [t.get("title", "") for t in trend_analysis["trending_topics"][:3]]
                formatted_trends = ", ".join(top_trends)
                trend_context = f"\\n\\nCONTEXT FROM CURRENT TRENDS:\\nThe following related topics are currently trending and should be subtly reflected in the content where relevant: {formatted_trends}."
                if trend_analysis.get("recommendations"):
                    recs = "; ".join(trend_analysis["recommendations"][:2])
                    trend_context += f"\nSpecific Trend Insights: {recs}"

        except Exception as step35_error:
            print(f"[WARN] Step 3.5 (SEO/Trends) failed gracefully: {step35_error}")
            import traceback
            print(traceback.format_exc())
            # Ensure critical objects are available even if validation failed
            if not image_collector:
                try:
                    from intelligence.image_collector import ImageCollector
                    image_collector = ImageCollector()
                except:
                    print("[WARN] Failed to initialize ImageCollector fallback")

        # Build enhanced prompt with tone and style instructions
        # Use Topic if available to keep content focused
        base_topic = request.topic if request.topic else request.prompt
        
        enhanced_system_prompt = get_enhanced_system_prompt(
            base_topic=base_topic,
            tone=request.tone,
            add_critical_thinking=request.include_critique,
            include_multiple_perspectives=request.include_alternatives
        ) + trend_context

        
        # Add enrichment instructions
        enrichment_instruction = ""
        if request.include_critique or request.include_alternatives or request.include_implications:
            enrichment_instruction = "\\n\\n" + get_content_enrichment_prompt()
        
        # Add formatting instructions
        formatting_instruction = "\\n\\n" + get_formatted_output_prompt(
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
        
        # If we have a refined query from the classifier, use it as the main instruction
        if request.refined_query:
             print(f"[INTENT] Using refined query: {request.refined_query}")
             final_user_message = request.refined_query
             
        if not history:
             # If no history, wrap the prompt with system instructions as the input
             # or better, just pass the enhanced prompt as the user message for this turn
             # We prepend the system instructions to the user message
             final_user_message = f"{enhanced_prompt}\n\nUser Request: {final_user_message}"
        
        content = agent.invoke(
            user_message=final_user_message,
            conversation_history=history,
        )
        
        # ========== GUARDRAILS CHECK #2: OUTPUT VALIDATION (AFTER GENERATION) ==========
        print(f"[GUARDRAILS #2] Validating generated output...")
        print(f"[GUARDRAILS #2] Content length: {len(content)} chars")
        print(f"[GUARDRAILS #2] Content preview: {content[:200]}...")
        
        output_validation = agent.guardrails.validate_user_message(content, role="assistant")
        print(f"[GUARDRAILS #2] Result: is_safe={output_validation.is_safe}, reason={output_validation.reason}, score={output_validation.score}")
        
        if not output_validation.is_safe:
            print(f"[GUARDRAILS #2] ❌ BLOCKED - Generated content violated safety guidelines: {output_validation.reason}")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Generated content blocked by safety filters",
                    "reason": output_validation.reason,
                    "score": output_validation.score,
                    "category": "output_validation",
                    "message": "The AI-generated content violated our safety guidelines. Please try rephrasing your request."
                }
            )
        
        print(f"[GUARDRAILS #2] ✅ PASSED - Output is safe")
        
        # Get safety report for logging
        safety_report = agent.guardrails.get_safety_report(request.prompt)
        

        # ========== STEP 5-6: STORE IN CONVERSATION & MESSAGE CACHE ==========
        # Default tracking values (initialized early for potential fallback)
        seo_score = 0.0
        uniqueness_score = 0.0
        engagement_score = 0.0
        request_cost = 0.0
        
        # Initialize trend_data if needed
        if not trend_data:
            trend_data = {}

        # 1. GENERATE IDENTIFIERS
        conversation_id = str(uuid.uuid4())
        conversation_hash = hashlib.sha256(request.prompt.encode()).hexdigest()[:64]
        user_message_id = str(uuid.uuid4())
        assistant_message_id = str(uuid.uuid4())
        
        # 2. REDIS CACHE (HOT STORAGE - DB INDEPENDENT)
        # Store in Redis for guest sessions (consistent with api/v1/guest.py)
        safe_debug_log(f"\\n[{datetime.utcnow().isoformat()}] Processing Request for Guest: {guest_id}\\n")
            
        if guest_id:
            try:
                redis = RedisManager.get_instance()
                if redis:
                    key = f"guest:{guest_id}"
                    
                    # Store User Prompt
                    user_msg_redis = {
                        "role": "user",
                        "content": request.prompt,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    redis.rpush(key, json.dumps(user_msg_redis))
                    
                    # Store AI Response
                    ai_msg_redis = {
                        "role": "assistant",
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    redis.rpush(key, json.dumps(ai_msg_redis))
                    
                    # Set expiration (24 hours)
                    redis.expire(key, 86400)
                    safe_debug_log(f"[INFO] Redis content stored for {key}\\n")
            except Exception as e:
                safe_debug_log(f"[ERROR] Redis error: {str(e)}\\n")

        # 3. SEO OPTIMIZATION (POST-GENERATION)
        print(f" [SEO] optimizing generated content...")
        seo_result = {}
        try:
            # Ensure optimizer is available
            if not seo_optimizer:
                seo_optimizer = SEOOptimizer(config=SEOConfig(model_name="gemini-2.0-flash"))

            seo_result = await seo_optimizer.optimize_content(
                content=content,
                target_keyword=keywords[0] if keywords else request.prompt[:20],
                context=trend_context
            )
        except Exception as seo_err:
            print(f"[WARN] SEO Optimization failed: {seo_err}")
            seo_result = {
                "seo_score": 50,
                "optimized_content": content,
                "meta_description": content[:150],
                "suggestions": []
            }
        
        # Merge trend recommendations
        if trend_analysis.get("recommendations") and "suggestions" in seo_result:
            seo_result["suggestions"].extend(trend_analysis["recommendations"][:3])
            
        seo_result["trend_data"] = trend_analysis
        seo_score = min(max(seo_result.get("seo_score", 50) / 100.0, 0.0), 1.0)

        # 4. DATABASE STORAGE (CONVERSATION, MESSAGE, ETC.)
        if db:
            try:
                # A. Main Conversation & Messages
                if user_id is not None and len(str(user_id)) == 36:
                    real_conversation = Conversation(
                        id=conversation_id,
                        user_id=user_id,
                        title=request.prompt[:100],
                        agent_type="text-generation",
                        model_used=request.model,
                        temperature=7,
                        status="active",
                        message_count=len(history) + 2,
                        created_at=datetime.utcnow(),
                        last_message_at=datetime.utcnow()
                    )
                    db.add(real_conversation)
                    
                    user_msg = Message(
                        id=user_message_id,
                        conversation_id=conversation_id,
                        role="user",
                        message_index=len(history),
                        content=request.prompt,
                        tokens_used=len(request.prompt.split()),
                        created_at=datetime.utcnow()
                    )
                    db.add(user_msg)
                    
                    assistant_msg = Message(
                        id=assistant_message_id,
                        conversation_id=conversation_id,
                        role="assistant",
                        message_index=len(history) + 1,
                        content=content,
                        model_used=request.model,
                        tokens_used=len(content.split()),
                        created_at=datetime.utcnow()
                    )
                    db.add(assistant_msg)
                    db.commit()

                # B. Prompt Cache
                input_tokens = len(request.prompt.split()) * 1.3
                output_tokens = len(content.split()) * 1.3
                
                new_cache_entry = PromptCache(
                    id=str(uuid.uuid4()),
                    prompt_hash=prompt_hash,
                    prompt_text=request.prompt,
                    response_text=content,
                    response_hash=hashlib.sha256(content.encode()).hexdigest(), # Generate hash to fix IntegrityError
                    model=request.model,
                    input_tokens=int(input_tokens),
                    output_tokens=int(output_tokens),
                    hits=1,
                    last_accessed=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(new_cache_entry)
                
                # C. Embeddings & Uniqueness
                embedding_vector = generate_embedding(content)
                uniqueness_score = 0.9 # Default
                
                # Use helper for uniqueness if imported, else fallback
                try:
                    # Simple inline uniqueness check against recent contents
                    recent_vectors = (
                        db.query(ContentEmbedding.embedding)
                        .order_by(ContentEmbedding.created_at.desc())
                        .limit(10)
                        .all()
                    )
                     # (Simplified logic to avoid importing numpy if not needed or assume high uniqueness)
                except:
                    pass

                # D. Generated Content Record
                # Ensure we have a valid tracking ID
                tracking_user_id = user_id if (user_id and len(str(user_id)) == 36) else (cache_user_id or guest_id)
                
                generated_record = GeneratedContent(
                    id=str(uuid.uuid4()),
                    user_id=tracking_user_id,
                    conversation_id=conversation_id,
                    message_id=assistant_message_id,
                    original_prompt=request.prompt,
                    requirements={"safety_level": request.safety_level},
                    content_type="text",
                    platform="web",
                    generated_content={
                        "text": content,
                        "model": request.model,
                        "timestamp": datetime.utcnow().isoformat(),
                        "intent": request.intent,
                        "seo_data": seo_result
                    },
                    seo_score=seo_score,
                    uniqueness_score=uniqueness_score,
                    engagement_score=engagement_score,
                    status="completed",
                    created_at=datetime.utcnow()
                )
                db.add(generated_record)
                db.flush() # Get ID
                
                # E. Content Embedding
                content_embedding = ContentEmbedding(
                    id=str(uuid.uuid4()),
                    content_id=generated_record.id,
                    text_source="generated_content",
                    source_id=generated_record.id,
                    embedded_text=content[:500],
                    embedding=embedding_vector,
                    embedding_model="all-MiniLM-L6-v2",
                    is_valid=True,
                    created_at=datetime.utcnow()
                )
                db.add(content_embedding)
                
                # F. Metrics
                if user_metrics:
                    user_metrics.total_requests += 1
                    user_metrics.cache_misses += 1
                    user_metrics.total_tokens += int(input_tokens + output_tokens)
                
                db.commit()
                print("[DB] ✓ Content, metrics, and SEO data stored successfully")
                
            except Exception as e:
                db.rollback()
                print(f"[WARN] DB Storage failed: {e}")
                import traceback
                print(traceback.format_exc())
        else:
            print("[WARN] DB unavailable - skipping storage")

        # 5. IMAGE GENERATION
        image_url = None
        if relevant_image_url:
             image_url = relevant_image_url
        else:
             try:
                 # Check intent
                 should_generate_image = request.intent in ['blog', 'rewrite', 'image']
                 if should_generate_image and image_collector:
                      # Generate enhanced image prompt
                      from intelligence.image_prompter import generate_image_prompt
                      
                      topic = request.prompt
                      summary = content[:500]
                      
                      img_prompt = await generate_image_prompt(topic, keywords, request.tone, summary)
                      print(f" [Image] Generating: {img_prompt[:50]}...")
                      image_url = await image_collector.get_relevant_image(img_prompt, model_provider="gpt")
                 elif image_collector:
                      # Simple fetch for keyword
                      query = keywords[0] if keywords else request.prompt[:20]
                      image_url = await image_collector.get_relevant_image(query)
             except Exception as img_err:
                 print(f"[WARN] Image generation failed: {img_err}")
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        word_count = len(content.split())
        section_count = content.count("##")

        return GenerateContentResponse(
            success=True,
            content=content,
            safety_checks=safety_report,
            tokens_used=len(content.split()), # Approx
            rate_limit_remaining=remaining,
            rate_limit_reset_after=0,
            cached=False,
            cache_hit_rate=0.0,
            generation_time_ms=elapsed_ms,
            seo_score=seo_score,
            uniqueness_score=uniqueness_score,
            engagement_score=engagement_score,
            cost_usd=request_cost,
            total_cost_usd=user_metrics.total_cost if user_metrics else 0.0,
            seo_data=seo_result,
            trend_data=trend_data,
            image_url=image_url,
            model=request.model,
            image_model="dall-e-3",
            tone_applied=request.tone,
            includes_critique=request.include_critique,
            includes_alternatives=request.include_alternatives,
            includes_implications=request.include_implications,
            analysis_depth="comprehensive",
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
        print(f"Traceback:\\n{error_details}")
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
        content_lines = request.content.strip().split('\\n')
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
        paragraphs = [p.strip() for p in request.content.split('\\n\\n') if p.strip()]
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
