"""
Guardrails API endpoints for message validation and safety checks.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.guardrails import get_message_guardrails

router = APIRouter(prefix="/v1/guardrails", tags=["guardrails"])


class ValidateMessageRequest(BaseModel):
    """Request to validate a message."""
    content: str
    role: str = "user"  # 'user', 'assistant', 'system'
    safety_level: str = "moderate"  # 'strict', 'moderate', 'permissive'


class ValidateSystemPromptRequest(BaseModel):
    """Request to validate system prompt."""
    prompt: str
    safety_level: str = "strict"  # System prompts should be strict


class SafetyReport(BaseModel):
    """Safety report for a message."""
    is_safe: bool
    reason: str
    score: float
    filtered_text: str


@router.post("/validate-message", response_model=SafetyReport)
async def validate_message(request: ValidateMessageRequest):
    """
    Validate a user message for safety.
    
    Args:
        request: ValidateMessageRequest with content, role, safety_level
        
    Returns:
        SafetyReport with validation result
    """
    try:
        guardrails = get_message_guardrails(request.safety_level)
        result = guardrails.validate_user_message(request.content, request.role)
        
        return SafetyReport(
            is_safe=result.is_safe,
            reason=result.reason,
            score=result.score,
            filtered_text=result.filtered_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-prompt", response_model=SafetyReport)
async def validate_prompt(request: ValidateSystemPromptRequest):
    """
    Validate a system prompt for safety.
    
    Args:
        request: ValidateSystemPromptRequest with prompt
        
    Returns:
        SafetyReport with validation result
    """
    try:
        guardrails = get_message_guardrails(request.safety_level)
        result = guardrails.validate_system_prompt(request.prompt)
        
        return SafetyReport(
            is_safe=result.is_safe,
            reason=result.reason,
            score=result.score,
            filtered_text=request.prompt if result.is_safe else ""
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_message(request: ValidateMessageRequest):
    """
    Get detailed safety analysis of a message.
    
    Args:
        request: ValidateMessageRequest with content
        
    Returns:
        Detailed safety report with all checks
    """
    try:
        guardrails = get_message_guardrails(request.safety_level)
        report = guardrails.get_safety_report(request.content)
        
        return {
            "message_preview": request.content[:100],
            "safety_analysis": report,
            "action": "allow" if report["overall"]["is_safe"] else "block"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-levels")
async def get_safety_levels():
    """Get available safety levels."""
    return {
        "levels": [
            {
                "name": "strict",
                "description": "Maximum filtering - blocks borderline content"
            },
            {
                "name": "moderate",
                "description": "Balanced filtering - recommended for most use cases"
            },
            {
                "name": "permissive",
                "description": "Minimal filtering - allows most content"
            }
        ]
    }
