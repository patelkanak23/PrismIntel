import sys
from pathlib import Path
from typing import Annotated, Dict, List

from langgraph.graph import StateGraph, START, END


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.state import ResearchState
from backend.agents.company import CompanyAnalyzer
from backend.agents.financial import FinancialAnalyst
from backend.agents.industry import IndustryAnalyzer
from backend.agents.news import NewsScanner
from backend.agents.risk import RiskScorer
from backend.agents.competitor import CompetitorAnalyst
from backend.nodes.grounding import grounding_node
from backend.nodes.collector import collector_node
from backend.nodes.curator import curator_node
from backend.nodes.briefing import briefing_node
from backend.nodes.editor import editor_node


def merge_documents(left: Dict[str, List[Dict]], right: Dict[str, List[Dict]]):
    return {**left, **right}


ResearchState.__annotations__["documents"] = Annotated[
    Dict[str, List[Dict]],
    merge_documents,
]


async def company_node(state):
    return await CompanyAnalyzer().run(state)


async def grounding_graph_node(state):
    result = await grounding_node(state)
    if result == {}:
        return {"documents": state.get("documents", {})}
    return result


async def financial_node(state):
    return await FinancialAnalyst().run(state)


async def industry_node(state):
    return await IndustryAnalyzer().run(state)


async def news_node(state):
    return await NewsScanner().run(state)


async def risk_node(state):
    return await RiskScorer().run(state)


async def competitor_node(state):
    return await CompetitorAnalyst().run(state)


graph = StateGraph(ResearchState)

graph.add_node("grounding", grounding_graph_node)
graph.add_node("company", company_node)
graph.add_node("financial", financial_node)
graph.add_node("industry_agent", industry_node)
graph.add_node("news", news_node)
graph.add_node("collector", collector_node)
graph.add_node("curator", curator_node)
graph.add_node("briefing", briefing_node)
graph.add_node("editor", editor_node)
graph.add_node("risk", risk_node)
graph.add_node("competitor", competitor_node)

graph.add_edge(START, "grounding")
graph.add_conditional_edges(
    "grounding",
    lambda state: ["company", "financial", "industry_agent", "news"],
    ["company", "financial", "industry_agent", "news"],
)
graph.add_edge(["company", "financial", "industry_agent", "news"], "collector")
graph.add_edge("collector", "curator")
graph.add_edge("curator", "briefing")
graph.add_edge("briefing", "editor")
graph.add_edge("editor", "risk")
graph.add_edge("risk", "competitor")
graph.add_edge("competitor", END)

app = graph.compile()


if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    from backend.state import create_initial_state

    async def test():
        print("Starting full pipeline test...")
        state = create_initial_state(
            job_id="pipeline_test_001",
            company_name="Tesla",
            industry="Electric Vehicles",
            hq_location="Austin TX",
        )
        result = await app.ainvoke(state)
        print("\n=== PIPELINE COMPLETE ===")
        assert result["final_report"] != ""
        assert result["risk_scores"] != {}
        assert len(result["competitors"]) == 3
        print(f"✅ Report: {len(result['final_report'])} chars")
        print(f"✅ Risk scores: {result['risk_scores']}")
        print(f"✅ Competitors: {len(result['competitors'])}")
        print("\nReport preview:")
        print(result["final_report"][:400])

    asyncio.run(test())
