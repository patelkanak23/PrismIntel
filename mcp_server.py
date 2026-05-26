import asyncio
import os
import sys
import uuid

from fastmcp import FastMCP


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.competitor import CompetitorAnalyst
from backend.agents.risk import RiskScorer
from backend.db.sqlite import get_history, init_db
from backend.graph import app as graph_app
from backend.state import create_initial_state


init_db()
mcp = FastMCP("PrismIntel — Company Intelligence")


@mcp.tool()
async def research_company(
    company_name: str,
    industry: str = "",
    website_url: str = "",
    hq_location: str = "",
) -> str:
    """
    Run full multi-agent research on a company.
    Returns a comprehensive markdown intelligence report
    covering company overview, financials, industry analysis,
    recent news, risk scores, and competitors.
    Takes 30-60 seconds to complete.
    """
    state = create_initial_state(
        job_id=str(uuid.uuid4()),
        company_name=company_name,
        website_url=website_url,
        industry=industry,
        hq_location=hq_location,
    )
    result = await graph_app.ainvoke(state)
    return result.get("final_report", "Research failed — no report generated")


@mcp.tool()
async def get_risk_score(company_name: str) -> dict:
    """
    Get risk scores for a company across four dimensions.
    Returns overall_risk, financial_risk, reputational_risk,
    market_risk (each scored 1-10) and a rationale string.
    Faster than full research.
    """
    state = create_initial_state(
        job_id=str(uuid.uuid4()),
        company_name=company_name,
    )
    scorer = RiskScorer()
    result = await scorer.run(state)
    return result.get("risk_scores", {})


@mcp.tool()
async def get_competitors(
    company_name: str,
    industry: str = "",
) -> list:
    """
    Find the top 3 competitors for a company.
    Returns a list of competitor dicts with name,
    description, and key strength.
    """
    state = create_initial_state(
        job_id=str(uuid.uuid4()),
        company_name=company_name,
        industry=industry,
    )
    agent = CompetitorAnalyst()
    result = await agent.run(state)
    return result.get("competitors", [])


@mcp.tool()
def get_research_history() -> list:
    """
    Get the last 10 companies researched with PrismIntel.
    Returns list of dicts with company_name, status, created_at.
    """
    return get_history()


if __name__ == "__main__":
    print("🔍 PrismIntel MCP Server starting on port 8001")
    print("Connect Claude Desktop to: http://localhost:8001/sse")
    mcp.run("sse", port=8001)
