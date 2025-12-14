from schemas import BlogRequest
from graph.blog_graph import blog_graph

async def run_blog_agent(req: BlogRequest):
    result = await blog_graph.ainvoke({
        "prompt": req.prompt,
        "tone": req.tone,
        "length": req.length,
    })
    return result