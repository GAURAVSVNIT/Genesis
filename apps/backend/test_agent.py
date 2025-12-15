import asyncio
import sys
sys.path.insert(0, 'e:/genesis/apps/backend')

from graph.blog_graph import blog_graph

async def test():
    result = await blog_graph.ainvoke({
        "prompt": "test blog about redis",
        "tone": "informative",
        "length": "short"
    })
    print("SUCCESS!")
    print(result)

asyncio.run(test())
