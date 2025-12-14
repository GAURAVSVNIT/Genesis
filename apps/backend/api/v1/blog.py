from fastapi import APIRouter
from pydantic import BaseModel
from agents.orchestrator import run_blog_agent

router= APIRouter()

from schemas import BlogRequest

@router.post("/generate")
async def generate_blog(req:BlogRequest):
    result = await run_blog_agent(req)
    return result 