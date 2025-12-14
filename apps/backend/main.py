from fastapi import FastAPI
from api.v1.blog import router as blog_router 

app = FastAPI(title="Genesis", description="Genesis API", version="1.0.0")

app.include_router(blog_router, prefix="/v1/blog")
