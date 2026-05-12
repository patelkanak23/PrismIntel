import os
import sys
from pathlib import Path


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
            competitors = [
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
        else:
            competitors = []

        return {"competitors": competitors}


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
