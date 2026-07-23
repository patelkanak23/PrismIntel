<div align="center">

# 🔍 PrismIntel

**AI-Powered Company Intelligence Platform**

*Multi-agent research system that generates professional intelligence reports on any company in under 60 seconds.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blue)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-prismintel.onrender.com-purple)](https://prismintel.onrender.com)

**[🔗 Live Demo → prismintel.onrender.com](https://prismintel.onrender.com)**

</div>

---

## What is PrismIntel?

PrismIntel is an **open-source intelligence platform** that researches any company using a team of specialized AI agents. Enter a company name, and PrismIntel dispatches six autonomous agents to gather data, analyze financials, map competitors, and compile everything into a structured intelligence report — the kind you'd expect from a professional research desk.

### ✨ Key Features

- **🤖 6 Specialized AI Agents** — Company, Financial, Industry, News, Risk, and Competitor analysts work in parallel
- **🌐 Live Web Research** — Real-time data collection via Tavily search API (not just LLM knowledge)
- **📊 Risk Scoring** — Automated 1-10 risk assessment across Financial, Reputational, and Market dimensions
- **🏢 Competitive Landscape** — LLM-powered competitor identification with descriptions and strengths
- **📋 Professional Reports** — Structured markdown reports with Executive Summary, subsections, and references
- **📥 PDF Export** — One-click download of the full report as PDF
- **🔌 MCP Server** — Use PrismIntel as a tool inside Claude Desktop or any MCP-compatible client
- **⚡ Real-time Streaming** — Watch the research progress live via Server-Sent Events (SSE)

---

## Architecture

PrismIntel uses a **LangGraph state machine** to orchestrate the research pipeline:

```
                        ┌─────────────┐
                        │  Grounding  │  ← Crawls company website
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────┴─────┐  ┌──────┴──────┐  ┌──────┴──────┐
        │  Company   │  │  Financial  │  │  Industry   │
        │  Analyzer  │  │  Analyst    │  │  Analyzer   │
        └─────┬─────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              │         ┌──────┴──────┐         │
              │         │    News     │         │
              │         │   Scanner   │         │
              │         └──────┬──────┘         │
              └────────────────┼────────────────┘
                               │
                        ┌──────┴──────┐
                        │  Collector  │  ← Merges all documents
                        └──────┬──────┘
                               │
                        ┌──────┴──────┐
                        │   Curator   │  ← Deduplicates & ranks
                        └──────┬──────┘
                               │
                        ┌──────┴──────┐
                        │  Briefing   │  ← LLM writes each section
                        └──────┬──────┘
                               │
                        ┌──────┴──────┐
                        │   Editor    │  ← Assembles final report
                        └──────┬──────┘
                               │
                  ┌────────────┼────────────┐
                  │                         │
           ┌──────┴──────┐          ┌───────┴───────┐
           │    Risk     │          │  Competitor   │
           │   Scorer    │          │   Analyst     │
           └──────┬──────┘          └───────┬───────┘
                  │                         │
                  └────────────┬────────────┘
                               │
                        ┌──────┴──────┐
                        │ Final Edit  │  ← Injects risk + competitors
                        └──────┬──────┘
                               │
                           📄 Report
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq (LLaMA 3.3 70B Versatile) |
| **Search** | Tavily AI (real-time web search) |
| **Orchestration** | LangGraph (multi-agent state machine) |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Vanilla HTML / CSS / JavaScript |
| **Database** | SQLite (research history) |
| **PDF Export** | FPDF2 |
| **MCP** | FastMCP (Claude Desktop integration) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/) (free tier works)
- A [Tavily API key](https://tavily.com/) (free tier works)

### Installation

```bash
# Clone the repository
git clone https://github.com/patelkanak23/PrismIntel.git
cd PrismIntel

# Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
USE_MOCKS=false
```

> **Note:** The Tavily API key is entered directly in the UI at runtime — it is not stored.

### Running

```bash
uvicorn backend.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Usage

1. **Enter your Tavily API key** in the key panel
2. **Fill in the company details** — only the company name is required
3. **Click "Start research"** and watch the agents work in real-time
4. **Review the report** — copy to clipboard or download as PDF

### MCP Server (Claude Desktop)

PrismIntel also works as a tool inside Claude Desktop:

```bash
python mcp_server.py
```

Connect Claude Desktop to `http://localhost:8001/sse`. You'll get access to:
- `research_company` — Full intelligence report
- `get_risk_score` — Quick risk assessment
- `get_competitors` — Competitor analysis
- `get_research_history` — Past research lookups

---

## Report Structure

Each generated report follows a professional analyst format:

| Section | Content |
|---------|---------|
| **Executive Summary** | High-level overview of the analysis |
| **Company Overview** | Corporate profile, products, leadership, business model, target markets |
| **Financial Overview** | Revenue, profitability, key metrics, dividends, outlook |
| **Industry Overview** | Market landscape, competitive environment, trends, challenges |
| **Recent Developments** | Material corporate news (filtered by analyst-grade materiality test) |
| **Risk Assessment** | Scored 1-10 across Overall, Financial, Reputational, and Market risk |
| **Competitive Landscape** | Top 3 direct competitors with descriptions and key strengths |
| **References** | Source URLs from web research |

---

## Project Structure

```
PrismIntel/
├── backend/
│   ├── main.py              # FastAPI app, routes, SSE streaming
│   ├── graph.py             # LangGraph pipeline definition
│   ├── state.py             # Research state schema
│   ├── events.py            # SSE event broadcasting
│   ├── agents/
│   │   ├── company.py       # Company profile agent
│   │   ├── financial.py     # Financial analysis agent
│   │   ├── industry.py      # Industry & market agent
│   │   ├── news.py          # News scanner agent
│   │   ├── risk.py          # Risk scoring agent
│   │   └── competitor.py    # Competitor analysis agent
│   ├── nodes/
│   │   ├── grounding.py     # Website crawling
│   │   ├── collector.py     # Document merging
│   │   ├── curator.py       # Deduplication & ranking
│   │   ├── briefing.py      # LLM briefing generation
│   │   └── editor.py        # Report assembly & formatting
│   ├── tools/
│   │   ├── llm.py           # Groq LLM wrapper with retry logic
│   │   └── tavily_tools.py  # Tavily search wrapper
│   └── db/
│       ├── __init__.py
│       └── sqlite.py        # SQLite history storage
├── frontend/
│   ├── index.html           # Main UI
│   ├── style.css            # Styling (dark theme, glassmorphism)
│   └── app.js               # Client logic, SSE, markdown renderer
├── mcp_server.py            # MCP server for Claude Desktop
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Limitations

- **Groq Free Tier:** 12,000 tokens per minute — may rate-limit with concurrent users (auto-retry with backoff is built in)
- **SQLite:** Research history is stored locally and will be lost if the server's disk is ephemeral (e.g., Render free tier)
- **Report Depth:** Dependent on what Tavily search returns and Groq's LLaMA 3.3 model capabilities

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## License

This project is open source under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ by <strong>Kanak Patel</strong></sub>
</div>
