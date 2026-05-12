import asyncio
import os
import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.state import ResearchState
from backend.tools.llm import get_llm


class RiskScorer:
    def __init__(self):
        self.llm = get_llm()

    async def run(self, state: ResearchState) -> dict:
        company = state["company_name"]
        print(f"RiskScorer running for: {company}")
        await asyncio.sleep(0.3)

        use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
        if use_mocks:
            scores = {
                "overall_risk": 4,
                "financial_risk": 3,
                "reputational_risk": 5,
                "market_risk": 4,
                "rationale": (
                    f"{company} shows stable fundamentals with moderate "
                    "market exposure across key risk dimensions."
                ),
            }
        else:
            scores = {}

        return {"risk_scores": scores}


if __name__ == "__main__":
    import asyncio
    from backend.state import create_initial_state

    async def test():
        agent = RiskScorer()
        state = create_initial_state("t001", "Tesla")
        result = await agent.run(state)
        scores = result["risk_scores"]
        assert scores["overall_risk"] == 4
        assert scores["financial_risk"] == 3
        assert scores["reputational_risk"] == 5
        assert scores["market_risk"] == 4
        assert "rationale" in scores
        print(f"✅ RiskScorer: {scores['overall_risk']} overall risk")
        print(f"   Rationale: {scores['rationale']}")

    asyncio.run(test())
