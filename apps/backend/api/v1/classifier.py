"""
Production-grade Intent Classifier using Google Vertex AI.

Classifies user prompts into 4 categories:
- 'chat': General conversation, questions, discussions
- 'blog': New blog/content creation requests
- 'modify': Modification/enhancement of existing content
- 'rewrite': Complete rewrite or fresh start from scratch

Uses Vertex AI's Gemini model for intelligent, context-aware classification.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from vertexai.generative_models import GenerativeModel
import vertexai
from core.config import settings
from core.upstash_redis import RedisManager
import json
import re

router = APIRouter()

# Initialize Vertex AI
try:
    if settings.GCP_PROJECT_ID:
        vertexai.init(project=settings.GCP_PROJECT_ID)
except Exception as e:
    print(f"Failed to initialize Vertex AI at module level: {e}")

# Redis for caching classifications
redis_manager = RedisManager()

# System prompt for classification
SYSTEM_PROMPT = """You are an expert intent classifier for an AI content generation platform.

Your task is to classify user prompts into one of four categories:

1. **CHAT**: General conversation, questions, advice, discussions
   - Examples: "What are the benefits of AI?", "How do I improve my writing?", "Tell me about marketing"
   - Keywords: ?, how, what, why, explain, discuss, help, tips, advice, question
   - Characteristics: User seeking information or having a conversation

2. **BLOG**: Request to create NEW content from scratch
   - Examples: "Write a blog about AI", "Create an article on climate change", "Generate a product description"
   - Keywords: write, create, generate, draft, compose, blog, article, post, content, story, guide
   - Characteristics: No existing content mentioned, starting fresh

3. **MODIFY**: Request to enhance/improve/edit EXISTING content
   - Examples: "Make it more professional", "Add more details", "Change the tone", "Improve the introduction"
   - Keywords: improve, enhance, better, add, more, increase, expand, polish, refine, better, strengthen
   - Characteristics: References to existing content, asking for incremental changes
   - Rule: Only if there IS existing content in context

4. **REWRITE**: Request for complete restart or fresh take from scratch
   - Examples: "Rewrite it completely", "Start over", "Write from scratch", "Completely new version"
   - Keywords: rewrite, restart, start over, from scratch, completely new, different angle, fresh approach
   - Characteristics: User wants to discard current approach and begin anew

Rules:
- If user says REWRITE/START OVER/FROM SCRATCH → REWRITE (ignore existing content, start fresh)
- If user says IMPROVE/ENHANCE/ADD/EXPAND with existing content → MODIFY (enhance current)
- If user says WRITE/CREATE/GENERATE → BLOG (new content)
- If user asks a QUESTION → CHAT
- Always check for rewrite keywords FIRST before defaulting to modify
- If previous content exists but user wants something fundamentally different → REWRITE

Respond with ONLY a JSON object (no additional text):
{
  "intent": "chat", "blog", "modify", or "rewrite",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation (one sentence)"
}"""


class IntentClassificationRequest(BaseModel):
    """Request model for intent classification."""
    prompt: str
    context_summary: str | None = None  # Optional: previous conversation context


class IntentClassificationResponse(BaseModel):
    """Response model for intent classification."""
    intent: Literal["chat", "blog", "modify", "rewrite"]
    confidence: float  # 0.0 to 1.0
    reasoning: str
    cached: bool = False


async def classify_with_vertex_ai(prompt: str, context_summary: str | None = None) -> dict:
    """
    Classify intent using Vertex AI Gemini model.
    
    Uses:
    - Fast Gemini Flash model for low latency
    - Structured output for consistency
    - Context for improved accuracy
    """
    
    user_message = f"""Classify this user prompt:

Prompt: "{prompt}"
"""
    
    if context_summary:
        user_message += f"""
Context of conversation:
{context_summary}
"""
    
    try:
        model = GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        response = model.generate_content(user_message)
        response_text = response.text.strip()
        
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "intent": result.get("intent", "chat"),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "")
            }
        else:
            # Fallback parsing
            if "blog" in response_text.lower():
                return {"intent": "blog", "confidence": 0.7, "reasoning": "Detected from response text"}
            else:
                return {"intent": "chat", "confidence": 0.6, "reasoning": "Default to chat"}
                
    except Exception as e:
        print(f"Error classifying with Vertex AI: {e}")
        # Fallback: simple keyword-based classification
        return classify_with_keywords(prompt)


def classify_with_keywords(prompt: str) -> dict:
    """
    Fallback keyword-based classification.
    Used when Vertex AI fails or for faster processing.
    """
    lower_prompt = prompt.lower()
    
    # Check for rewrite keywords FIRST (highest priority)
    rewrite_keywords = ['rewrite', 'restart', 'start over', 'from scratch', 'completely new', 'fresh', 'different angle', 'anew']
    if any(keyword in lower_prompt for keyword in rewrite_keywords):
        return {
            "intent": "rewrite",
            "confidence": 0.9,
            "reasoning": "Detected rewrite keywords"
        }
    
    # Check for modify keywords
    modify_keywords = ['improve', 'enhance', 'better', 'add', 'more', 'expand', 'polish', 'refine', 'strengthen', 'update', 'modify', 'edit']
    modify_score = sum(1 for keyword in modify_keywords if keyword in lower_prompt)
    
    # Check for chat indicators
    chat_indicators = ['?', 'how', 'what', 'why', 'explain', 'tell me', 'help', 'tips', 'advice']
    chat_score = sum(1 for indicator in chat_indicators if indicator in lower_prompt)
    
    # Check for blog creation keywords
    blog_keywords = ['write', 'create', 'generate', 'draft', 'compose', 'blog', 'article', 'post', 'content', 'story', 'guide', 'tutorial', 'email', 'copy', 'description', 'caption', 'headline', 'title', 'outline']
    blog_score = sum(1 for keyword in blog_keywords if keyword in lower_prompt)
    
    # Determine intent based on scores
    if modify_score > 0:
        intent = "modify"
        confidence = min(0.9, 0.5 + (modify_score * 0.15))
    elif blog_score > chat_score:
        intent = "blog"
        confidence = min(0.95, 0.5 + (blog_score * 0.1))
    elif chat_score > 0:
        intent = "chat"
        confidence = min(0.95, 0.5 + (chat_score * 0.1))
    else:
        intent = "chat"
        confidence = 0.5
    
    return {
        "intent": intent,
        "confidence": round(confidence, 2),
        "reasoning": "Keyword-based classification (fallback)"
    }


@router.post("/v1/classify/intent", response_model=IntentClassificationResponse)
async def classify_intent(request: IntentClassificationRequest) -> IntentClassificationResponse:
    """
    Classify user prompt as 'chat' or 'blog' intent.
    
    Production-grade classifier using Vertex AI Gemini for intelligent,
    context-aware classification.
    
    Request:
    - prompt: The user's message
    - context_summary: Optional conversation context for better accuracy
    
    Response:
    - intent: 'chat' or 'blog'
    - confidence: 0.0-1.0 confidence score
    - reasoning: Explanation of classification
    - cached: Whether result was cached
    """
    
    # Create cache key
    cache_key = f"intent_classification:{hash(request.prompt + (request.context_summary or ''))}"
    
    try:
        # Try to get from cache
        cached_result = redis_manager.get(cache_key)
        if cached_result:
            cached_data = json.loads(cached_result)
            return IntentClassificationResponse(
                **cached_data,
                cached=True
            )
    except Exception as e:
        print(f"Cache read error: {e}")
    
    # Classify using Vertex AI
    classification = await classify_with_vertex_ai(request.prompt, request.context_summary)
    
    response = IntentClassificationResponse(
        intent=classification["intent"],
        confidence=classification["confidence"],
        reasoning=classification["reasoning"],
        cached=False
    )
    
    # Cache result for 24 hours
    try:
        redis_manager.setex(
            cache_key,
            86400,  # 24 hours
            json.dumps({
                "intent": response.intent,
                "confidence": response.confidence,
                "reasoning": response.reasoning
            })
        )
    except Exception as e:
        print(f"Cache write error: {e}")
    
    return response


@router.get("/v1/classify/health")
async def classifier_health():
    """Health check for classifier service."""
    try:
        # Test Vertex AI
        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hi")
        return {
            "status": "healthy",
            "classifier": "operational",
            "model": "gemini-1.5-flash",
            "provider": "vertex-ai"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "classifier": "error",
            "error": str(e),
            "provider": "vertex-ai"
        }
