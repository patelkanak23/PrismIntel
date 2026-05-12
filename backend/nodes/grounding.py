from backend.state import ResearchState
from backend.tools.tavily_tools import get_search_tool


async def grounding_node(state: ResearchState) -> dict:
    url = state.get("website_url", "")
    if not url:
        print("Grounding: no URL provided, skipping")
        return {}
    print(f"Grounding: crawling {url}")
    try:
        tool = get_search_tool()
        content = await tool.crawl(url)
        doc = {
            "title": "Company Homepage",
            "url": url,
            "content": content,
            "score": 1.0,
        }
        existing = state.get("documents", {})
        return {"documents": {**existing, "website": [doc]}}
    except Exception as e:
        print(f"Grounding: crawl failed — {e}")
        return {"errors": state.get("errors", []) + [str(e)]}
