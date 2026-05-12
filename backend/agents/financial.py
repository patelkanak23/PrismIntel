import sys
from pathlib import Path
from typing import Dict, List


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.state import ResearchState
from backend.tools.llm import get_llm
from backend.tools.tavily_tools import get_search_tool


class FinancialAnalyst:
    def __init__(self):
        self.llm = get_llm()
        self.search_tool = get_search_tool()
        self.category = "financial"

    async def generate_queries(self, company_name: str) -> List[str]:
        return [
            f"{company_name} revenue profitability financial performance 2024",
            f"{company_name} funding valuation investor relations",
            f"{company_name} earnings margins cash flow growth",
            f"{company_name} financial outlook analyst expectations",
        ]

    async def search(self, queries: List[str]) -> List[Dict]:
        all_results = []
        seen_urls = set()
        for query in queries:
            results = await self.search_tool.search(query, topic="finance")
            for doc in results:
                if doc["url"] not in seen_urls:
                    seen_urls.add(doc["url"])
                    all_results.append(doc)
        print(f"FinancialAnalyst: {len(all_results)} unique docs")
        return all_results

    async def run(self, state: ResearchState) -> dict:
        company = state["company_name"]
        print(f"FinancialAnalyst starting for: {company}")
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
        agent = FinancialAnalyst()
        state = create_initial_state("t001", "Tesla")
        result = await agent.run(state)
        docs = result["documents"]["financial"]
        assert len(docs) > 0
        assert "title" in docs[0]
        assert "url" in docs[0]
        assert "score" in docs[0]
        print(f"✅ FinancialAnalyst: {len(docs)} docs")
        print(f"   First: {docs[0]['title']}")

    asyncio.run(test())
