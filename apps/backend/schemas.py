from pydantic import BaseModel
from typing import Optional

class BlogRequest(BaseModel):
    prompt: str
    tone: str = "informative"
    length: str = "medium"
    guestId: Optional[str] = None  # For guest users, optional for authenticated

class AgentRequest(BaseModel):
    task: str
