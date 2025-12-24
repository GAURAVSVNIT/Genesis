"""
API Improvement Guide: Token Counting and Error Handling
Update api/v1/content.py to use these improvements
"""

# IMPROVEMENT 1: Replace imports at top of content.py
# Add after existing imports:
"""
from core.token_counter import get_token_counter, calculate_cost
from core.logging_handler import StructuredLogger, ErrorHandler, PerformanceMonitor
"""

# IMPROVEMENT 2: Replace token counting function
"""
OLD CODE (inaccurate):
    input_tokens = len(request.prompt.split())
    output_tokens = len(content_str.split())

NEW CODE (accurate):
    token_counter = get_token_counter()
    input_tokens = token_counter.count_tokens(request.prompt)
    output_tokens = token_counter.count_tokens(content_str)
"""

# IMPROVEMENT 3: Replace cost calculation
"""
OLD CODE:
    request_cost = calculate_cost("gemini-2.0-flash", input_tokens, output_tokens)

NEW CODE:
    from core.token_counter import calculate_cost
    request_cost = calculate_cost("gemini-2.0-flash", input_tokens, output_tokens)

The function is already there and improved!
"""

# IMPROVEMENT 4: Add structured logging
"""
Add at top of generate_content function:
    logger = StructuredLogger("content_generation")
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Content generation request received",
        request_id=request_id,
        prompt_length=len(request.prompt)
    )

Then replace all print() statements with:
    logger.info("Message", context=data)
    logger.error("Error", error=str(e), request_id=request_id)
"""

# IMPROVEMENT 5: Add performance monitoring
"""
Wrap the main generation in:
    with PerformanceMonitor(f"Content Generation [{request_id}]") as perf:
        # ... existing code ...
        elapsed_ms = perf.duration_ms
"""

# IMPROVEMENT 6: Improve error handling
"""
Replace generic try/except:

OLD:
    try:
        # ... code ...
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

NEW:
    try:
        # ... code ...
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        error = ErrorHandler.handle_validation_error(e, {"request_id": request_id})
        logger.warning("Validation error", error=str(e), request_id=request_id)
        raise HTTPException(status_code=400, detail=error)
    except SQLAlchemyError as e:
        db.rollback()
        error = ErrorHandler.handle_database_error(e, "content generation", {"request_id": request_id})
        logger.error("Database error", error=str(e), request_id=request_id, exc_info=True)
        raise HTTPException(status_code=500, detail=error)
    except Exception as e:
        db.rollback()
        error = ErrorHandler.handle_generic_error(e, "content generation", {"request_id": request_id})
        logger.error("Unexpected error", error=str(e), request_id=request_id, exc_info=True)
        raise HTTPException(status_code=500, detail=error)
"""

# IMPROVEMENT 7: Standardize response format
"""
All responses should follow:
    {
        "success": bool,
        "data": {...},
        "metadata": {
            "request_id": str,
            "timestamp": str,
            "duration_ms": int
        },
        "error": null or {...}
    }

Instead of current mixed format.
"""

# IMPROVEMENT 8: Add input validation
"""
Add validation function:

def validate_content_request(request: GenerateContentRequest) -> tuple[bool, Optional[str]]:
    '''Validate request before processing.'''
    # Check prompt length
    if not request.prompt or len(request.prompt.strip()) == 0:
        return False, "Prompt cannot be empty"
    
    if len(request.prompt) > 10000:
        return False, "Prompt too long (max 10000 characters)"
    
    # Check safety level
    valid_levels = ["strict", "moderate", "permissive"]
    if request.safety_level not in valid_levels:
        return False, f"Invalid safety_level. Must be one of {valid_levels}"
    
    return True, None

Then in generate_content():
    is_valid, error_msg = validate_content_request(request)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
"""

# IMPROVEMENT 9: Add database health check
"""
Add before any database operation:

def check_database_health() -> bool:
    '''Quick database connectivity check.'''
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False
"""

# IMPROVEMENT 10: Add comprehensive endpoint documentation
"""
Improve the docstring in generate_content to include:
    
    Args:
        request: GenerateContentRequest with:
            - prompt (str): 1-10000 characters
            - conversation_history (List[Message]): max 10 messages
            - safety_level (str): 'strict', 'moderate', 'permissive'
        http_request: FastAPI Request context
        db: Database session
        
    Returns:
        GenerateContentResponse with:
            - success (bool): Whether generation succeeded
            - content (str): Generated content
            - safety_checks (dict): Safety validation results
            - seo_score (float): 0-1 SEO quality
            - uniqueness_score (float): 0-1 plagiarism check
            - engagement_score (float): 0-1 engagement prediction
            - cost_usd (float): API cost
            - generation_time_ms (int): Duration
            - cached (bool): Whether from cache
            - cache_hit_rate (float): System cache hit rate
            - tokens_used (int): Total tokens
            - rate_limit_remaining (int): Remaining requests
            
    Raises:
        HTTPException 400: Validation error
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error
        
    Example:
        >>> response = await generate_content(
        ...     GenerateContentRequest(
        ...         prompt="Write about AI ethics",
        ...         safety_level="moderate"
        ...     ),
        ...     http_request,
        ...     db
        ... )
        >>> print(response.seo_score)  # 0.75
"""

# IMPROVEMENT 11: Add database transaction safety
"""
Replace generic db.commit() with:

try:
    db.commit()
    logger.info("Database transaction committed", request_id=request_id)
except Exception as e:
    db.rollback()
    logger.error("Transaction commit failed, rolling back", error=str(e))
    raise
"""

# IMPROVEMENT 12: Cache invalidation strategy
"""
When storing content, mark related cache as potentially stale:

def invalidate_related_cache(db: Session, keywords: List[str]):
    '''Invalidate cache entries related to keywords.'''
    # For exact match, no action needed
    # For semantic similar, would query embeddings here
    # Current implementation: just log
    logger.debug(f"Cache invalidation hook called for {keywords}")
"""

# SUMMARY OF CHANGES
"""
Priority of Implementation:

CRITICAL (Do First):
1. Token counting accuracy (use token_counter.py)
2. Error handling standardization
3. Structured logging

IMPORTANT (Do Second):
4. Input validation
5. Database health check
6. Response format standardization

NICE TO HAVE (Optional):
7. Performance monitoring
8. Better documentation
9. Cache invalidation
10. Transaction safety improvements

Estimated time: 4-6 hours total
Risk level: Low (backward compatible)
Benefits: Better reliability, debugging, and production readiness
"""
