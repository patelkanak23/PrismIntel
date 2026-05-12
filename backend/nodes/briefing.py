import asyncio

from backend.state import ResearchState
from backend.tools.llm import get_llm


async def briefing_node(state: ResearchState) -> dict:
    llm = get_llm()
    company = state["company_name"]
    categories = ["company", "financial", "industry", "news"]

    async def brief_one(category):
        docs = state.get("curated_docs", {}).get(category, [])
        print(f"Briefing: generating {category} briefing...")
        result = await llm.generate_briefing(category, company, docs)
        print(f"Briefing: {category} done")
        return category, result

    results = await asyncio.gather(*[brief_one(c) for c in categories])
    briefings = dict(results)
    return {"briefings": briefings}
