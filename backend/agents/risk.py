import asyncio
import json
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
            scores = self._fallback_scores(company)
        else:
            scores = await self._score_with_llm(state)

        return {"risk_scores": scores}

    async def _score_with_llm(self, state: ResearchState) -> dict:
        company = state["company_name"]
        report = state.get("final_report", "")
        prompt = (
            f"Score {company}'s risk profile using this intelligence report. "
            "Return only valid JSON with keys overall_risk, financial_risk, "
            "reputational_risk, market_risk as integers from 1 to 10, plus "
            "rationale as one concise sentence.\n\n"
            f"{report[:6000]}"
        )
        try:
            text = await self.llm.generate(prompt)
            start = text.find("{")
            end = text.rfind("}") + 1
            data = json.loads(text[start:end])
            return {
                "overall_risk": int(data.get("overall_risk", 4)),
                "financial_risk": int(data.get("financial_risk", 3)),
                "reputational_risk": int(data.get("reputational_risk", 5)),
                "market_risk": int(data.get("market_risk", 4)),
                "rationale": data.get(
                    "rationale",
                    self._fallback_scores(company)["rationale"],
                ),
            }
        except Exception as e:
            print(f"RiskScorer LLM scoring failed: {e}")
            return self._fallback_scores(company)

    def _fallback_scores(self, company: str) -> dict:
        return {
            "overall_risk": 4,
            "financial_risk": 3,
            "reputational_risk": 5,
            "market_risk": 4,
            "rationale": (
                f"{company} shows stable fundamentals with moderate "
                "market exposure across key risk dimensions."
            ),
        }


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
