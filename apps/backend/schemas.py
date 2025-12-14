from pydantic import BaseModel

class BlogRequest(BaseModel):
    prompt: str
    tone: str = "informative"
    length: str = "medium"
