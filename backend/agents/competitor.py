import os
import sys
from pathlib import Path
from urllib.parse import urlparse


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.state import ResearchState
from backend.tools.tavily_tools import get_search_tool


class CompetitorAnalyst:
    def __init__(self):
        self.search_tool = get_search_tool()

    async def run(self, state: ResearchState) -> dict:
        company = state["company_name"]
        industry = state.get("industry", "")
        print(f"CompetitorAnalyst running for: {company}")

        use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
        if use_mocks:
            competitors = self._fallback_competitors(company, industry)
        else:
            competitors = await self._find_competitors(company, industry)

        return {"competitors": competitors}

    async def _find_competitors(self, company: str, industry: str) -> list:
        query = f"{company} competitors {industry} major rivals"
        try:
            results = await self.search_tool.search(query)
            competitors = []
            seen_names = set()
            for result in results:
                name = self._name_from_result(result)
                if not name or name.lower() in seen_names or name.lower() == company.lower():
                    continue
                seen_names.add(name.lower())
                competitors.append({
                    "name": name,
                    "description": result.get(
                        "content",
                        f"Potential competitor to {company}",
                    )[:220],
                    "strength": "Market visibility and comparable positioning",
                })
                if len(competitors) == 3:
                    break
            return competitors or self._fallback_competitors(company, industry)
        except Exception as e:
            print(f"Competitor search failed: {e}")
            return self._fallback_competitors(company, industry)

    def _name_from_result(self, result: dict) -> str:
        title = result.get("title", "").split("|")[0].split(":")[0].strip()
        if title:
            return title[:80]
        url = result.get("url", "")
        domain = urlparse(url).netloc.replace("www.", "")
        return domain.split(".")[0].title() if domain else ""

    def _fallback_competitors(self, company: str, industry: str) -> list:
        return [
            {
                "name": f"{company} Competitor A",
                "description": f"Leading alternative to {company}",
                "strength": "Established market presence",
            },
            {
                "name": f"{company} Competitor B",
                "description": f"Fast-growing rival in {industry}",
                "strength": "Innovation and pricing",
            },
            {
                "name": f"{company} Competitor C",
                "description": f"International competitor to {company}",
                "strength": "Global distribution network",
            },
        ]


if __name__ == "__main__":
    import asyncio
    from backend.state import create_initial_state

    async def test():
        agent = CompetitorAnalyst()
        state = create_initial_state("t001", "Tesla", industry="electric vehicles")
        result = await agent.run(state)
        competitors = result["competitors"]
        assert len(competitors) == 3
        assert "name" in competitors[0]
        assert "description" in competitors[0]
        assert "strength" in competitors[0]
        print(f"✅ CompetitorAnalyst: {len(competitors)} competitors")
        print(f"   First: {competitors[0]['name']}")

    asyncio.run(test())
