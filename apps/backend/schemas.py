from pydantic import BaseModel

class BlogRequest(BaseModel):
    prompt: str
    tone: str = "informative"
    length: str = "medium"

class AgentRequest(BaseModel):
    task: str
