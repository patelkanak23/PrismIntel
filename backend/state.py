from typing import TypedDict, Dict, List, Optional, Any


class ResearchState(TypedDict):
    job_id: str  # unique UUID per research job
    company_name: str  # required user input
    website_url: str  # optional company homepage to crawl
    industry: str  # optional industry context for focused research
    hq_location: str  # optional geographic context
    status: str  # pending, running, complete, or error
    documents: Dict[str, List[Dict]]  # raw docs keyed by category
    curated_docs: Dict[str, List[Dict]]  # filtered and ranked docs
    briefings: Dict[str, str]  # LLM markdown per category
    final_report: str  # compiled full markdown report
    risk_scores: Dict[str, Any]  # risk dimensions scored from 1 to 10
    competitors: List[Dict]  # top competitor dictionaries
    events: List[Dict]  # SSE events emitted so far
    errors: List[str]  # non-fatal pipeline errors
    created_at: str  # ISO 8601 timestamp


async def create_initial_state():
    return None
