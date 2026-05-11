from fastmcp import FastMCP


mcp = FastMCP("PrismIntel")


@mcp.tool()
async def research_company(company_name, industry, website_url, hq_location):
    return None


@mcp.tool()
async def get_risk_score(company_name):
    return None


@mcp.tool()
async def get_competitors(company_name, industry):
    return None


@mcp.tool()
async def get_research_history():
    return None
