# PrismIntel — Project Context

## What This Is
PrismIntel is a multi-agent company intelligence platform.
Users enter a company name. A LangGraph pipeline of 6 specialized
AI agents researches the company and produces a structured
intelligence report with risk scores and competitor analysis.

## Tech Stack
| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | Pure HTML + CSS + minimal JS (SSE)  |
| Backend    | FastAPI (serves frontend + API)     |
| Agents     | LangGraph                           |
| LLM        | Groq — llama-3.1-70b-versatile      |
| Search     | Tavily API                          |
| Database   | SQLite (standard library)           |
| Streaming  | Server-Sent Events (SSE)            |
| PDF        | fpdf2                               |
| Tracing    | LangSmith                           |
| MCP        | fastmcp (exposes tools to AI agents)|

## Folder Structure
```
prismintel/
  backend/
    main.py              ← FastAPI app, all endpoints, serves frontend
    graph.py             ← LangGraph StateGraph definition
    state.py             ← ResearchState TypedDict + create_initial_state()
    events.py            ← SSE EventManager (queue per job)
    agents/
      __init__.py
      company.py         ← CompanyAnalyzer
      financial.py       ← FinancialAnalyst
      industry.py        ← IndustryAnalyzer
      news.py            ← NewsScanner
      risk.py            ← RiskScorer
      competitor.py      ← CompetitorAnalyst
    nodes/
      __init__.py
      grounding.py       ← crawl company website
      collector.py       ← merge all agent results
      curator.py         ← filter score<0.4, keep top 20
      briefing.py        ← LLM summaries per category
      editor.py          ← compile final markdown report
    tools/
      __init__.py
      llm.py             ← BaseLLM + MockLLM + GroqLLM + get_llm()
      tavily_tools.py    ← BaseSearchTool + MockTavily + RealTavily + get_search_tool()
    db/
      __init__.py
      sqlite.py          ← init_db(), save_job(), get_history()
  frontend/
    index.html           ← single page, all layout and structure
    style.css            ← all styling, dark theme, professional look
    app.js               ← ONLY SSE connection + DOM updates (minimal)
  mcp_server.py          ← FastMCP server exposing 4 research tools
  tests/
    test_state.py
    test_llm.py
    test_tavily.py
    test_company_agent.py
  requirements.txt
  .env
  .gitignore
  CONTEXT.md             ← this file — never delete, never modify rules
  TASKS.md               ← progress tracker, update after every task
  README.md
```

## Engineering Rules (NEVER violate)
1. All backend code must be async (async def everywhere)
2. USE_MOCKS=true → all fake data, zero real API calls
3. USE_MOCKS=false → real Groq + real Tavily APIs
4. Every LangGraph node receives state dict, returns dict of updates only
5. State is the ONLY communication channel between nodes — no globals
6. NEVER use OpenAI. NEVER use Gemini. Only Groq.
7. NEVER use MongoDB. Only SQLite via standard library sqlite3.
8. NEVER use React. NEVER use Streamlit. Frontend is pure HTML/CSS/JS.
9. JS in frontend/app.js does ONE thing only: SSE connection + DOM updates.
10. One feature per Codex task. Never combine features in one task.
11. Always include a runnable test at the bottom of every implemented file.
12. Always commit after every passing test before moving to next task.

## ResearchState Fields
```python
class ResearchState(TypedDict):
    job_id: str              # unique UUID per research job
    company_name: str        # required user input
    website_url: str         # optional — company homepage to crawl
    industry: str            # optional — helps agents focus queries
    hq_location: str         # optional — geographic context
    status: str              # pending | running | complete | error
    documents: Dict[str, List[Dict]]   # raw docs keyed by category
    curated_docs: Dict[str, List[Dict]] # filtered + ranked docs
    briefings: Dict[str, str]          # LLM markdown per category
    final_report: str        # compiled full markdown report
    risk_scores: Dict[str, Any]        # risk dimensions 1-10
    competitors: List[Dict]  # top 3 competitor dicts
    events: List[Dict]       # SSE events emitted so far
    errors: List[str]        # non-fatal errors, pipeline continues
    created_at: str          # ISO 8601 timestamp
```

## Document Contract
Every document anywhere in the system must match exactly:
```python
{
    "title": str,      # readable title
    "url":   str,      # source URL, used for deduplication
    "content": str,    # full text content
    "score": float     # relevance 0.0 to 1.0
}
```

## LangGraph Pipeline Order
```
START
  → grounding_node          (crawl website if URL provided)
  → company_node   ─┐
  → financial_node  ├─ PARALLEL (all 4 run simultaneously)
  → industry_node   │
  → news_node      ─┘
  → collector_node          (merge all documents into state)
  → curator_node            (filter score<0.4, top 20 per category)
  → briefing_node           (LLM summaries, asyncio.gather for speed)
  → editor_node             (compile briefings into final report)
  → risk_node               (score 1-10 across 4 dimensions)
  → competitor_node         (find top 3 competitors)
  → END
```

## FastAPI Endpoints
```
POST   /research                  → accepts ResearchRequest, returns job_id (202)
GET    /research/{job_id}/stream  → SSE stream, emits typed events
GET    /research/{job_id}/report  → returns report or {status: pending}
GET    /history                   → last 10 jobs from SQLite
POST   /generate-pdf              → accepts {markdown: str}, returns PDF bytes
GET    /                          → serves frontend/index.html
GET    /static/{file}             → serves frontend/style.css and frontend/app.js
```

## SSE Event Types and Payloads
```python
{"type": "progress",            "data": {"message": str, "pct": int}}
{"type": "crawl_start",         "data": {"url": str}}
{"type": "crawl_success",       "data": {"url": str, "chars": int}}
{"type": "crawl_error",         "data": {"url": str, "error": str}}
{"type": "query_generating",    "data": {"agent": str}}
{"type": "query_generated",     "data": {"agent": str, "queries": list}}
{"type": "briefing_start",      "data": {"category": str}}
{"type": "briefing_complete",   "data": {"category": str}}
{"type": "risk_score",          "data": {"scores": dict}}
{"type": "competitor_analysis", "data": {"competitors": list}}
{"type": "complete",            "data": {"report": str}}
{"type": "error",               "data": {"message": str}}
```

## Frontend Rules (HTML/CSS/JS)
- index.html: all page structure, semantic HTML5, no inline styles, no inline JS
- style.css: all visual styling, dark theme using CSS variables
- app.js: ONLY handles SSE connection and updating DOM elements by ID
- app.js must NOT contain business logic, routing, or state management
- form submission is a standard HTML form POST — no fetch in the form handler
- SSE is the only reason JS exists — if browser supported SSE natively via HTML, we would not need JS at all
- Every interactive element has a clear HTML id attribute
- No npm. No build step. No bundler. Files served directly by FastAPI StaticFiles.

## MCP Server
```
File:      mcp_server.py (project root)
Library:   fastmcp
Port:      8001
Transport: SSE (HTTP accessible)
Run:       python mcp_server.py

Tools exposed:
  research_company(company_name, industry, website_url, hq_location) → str
    Runs full LangGraph pipeline, returns markdown report

  get_risk_score(company_name) → dict
    Runs only RiskScorer agent, returns risk dict

  get_competitors(company_name, industry) → list
    Runs only CompetitorAnalyst, returns list of 3 dicts

  get_research_history() → list
    Returns last 10 jobs from SQLite

Claude Desktop config (add to claude_desktop_config.json):
  {
    "mcpServers": {
      "prismintel": {
        "url": "http://localhost:8001/sse",
        "transport": "sse"
      }
    }
  }
```

## Mock Contracts
When USE_MOCKS=true every mock must return data matching real contracts:

MockLLM.generate_queries("Tesla") must return:
```python
["Tesla company overview business model 2024",
 "Tesla leadership team executives",
 "Tesla products services revenue streams",
 "Tesla corporate strategy expansion plans"]
```

MockTavily.search("any query") must return:
```python
[
  {"title": "...", "url": "https://bloomberg.com/...",
   "content": "...", "score": 0.92},
  {"title": "...", "url": "https://techcrunch.com/...",
   "content": "...", "score": 0.78},
  {"title": "...", "url": "https://reuters.com/...",
   "content": "...", "score": 0.65}
]
```

RiskScorer mock must return:
```python
{
  "overall_risk": 4,
  "financial_risk": 3,
  "reputational_risk": 5,
  "market_risk": 4,
  "rationale": "Stable company with moderate market exposure."
}
```

## Requirements (pinned versions)
```
fastapi==0.111.0
uvicorn==0.29.0
langgraph==0.1.19
langchain==0.2.5
langchain-groq==0.1.6
tavily-python==0.3.3
httpx==0.27.0
fpdf2==2.7.9
python-dotenv==1.0.1
pydantic==2.7.1
fastmcp==0.1.0
```

## Environment Variables (.env)
```
GROQ_API_KEY=        # free at console.groq.com
TAVILY_API_KEY=      # free at tavily.com
LANGCHAIN_API_KEY=   # free at smith.langchain.com
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=prismintel
USE_MOCKS=true       # change to false when real APIs ready
```

## How to Run
```bash
# Terminal 1 — main app (API + frontend)
uvicorn backend.main:app --reload --port 8000
# Visit: http://localhost:8000

# Terminal 2 — MCP server (optional, for Claude Desktop)
python mcp_server.py
# Connect at: http://localhost:8001/sse
```

## Three Entry Points
1. Browser UI  → http://localhost:8000
2. REST API    → POST http://localhost:8000/research
3. MCP tools   → http://localhost:8001/sse (Claude Desktop etc)