import sys
from pathlib import Path
from typing import Dict, List


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.state import ResearchState
from backend.tools.llm import get_llm
from backend.tools.tavily_tools import get_search_tool


class CompanyAnalyzer:
    def __init__(self):
        self.llm = get_llm()
        self.search_tool = get_search_tool()
        self.category = "company"

    async def generate_queries(self, company_name: str) -> List[str]:
        queries = await self.llm.generate_queries(company_name)
        return queries

    async def search(self, queries: List[str]) -> List[Dict]:
        all_results = []
        seen_urls = set()
        for query in queries:
            results = await self.search_tool.search(query)
            for doc in results:
                if doc["url"] not in seen_urls:
                    seen_urls.add(doc["url"])
                    all_results.append(doc)
        print(f"CompanyAnalyzer: {len(all_results)} unique docs")
        return all_results

    async def run(self, state: ResearchState) -> dict:
        company = state["company_name"]
        print(f"CompanyAnalyzer starting for: {company}")
        queries = await self.generate_queries(company)
        documents = await self.search(queries)
        existing = state.get("documents", {})
        return {
            "documents": {**existing, self.category: documents}
        }


if __name__ == "__main__":
    import asyncio
    from backend.state import create_initial_state

    async def test():
        agent = CompanyAnalyzer()
        state = create_initial_state("t001", "Tesla")
        result = await agent.run(state)
        docs = result["documents"]["company"]
        assert len(docs) > 0
        assert "title" in docs[0]
        assert "url" in docs[0]
        assert "score" in docs[0]
        print(f"✅ CompanyAnalyzer: {len(docs)} docs")
        print(f"   First: {docs[0]['title']}")

    asyncio.run(test())
