from datetime import datetime
from typing import Any, Dict, List, TypedDict


class ResearchState(TypedDict):
    job_id: str
    company_name: str
    website_url: str
    industry: str
    hq_location: str
    status: str
    documents: Dict[str, List[Dict]]
    curated_docs: Dict[str, List[Dict]]
    briefings: Dict[str, str]
    final_report: str
    risk_scores: Dict[str, Any]
    competitors: List[Dict]
    events: List[Dict]
    errors: List[str]
    created_at: str


def create_initial_state(
    job_id,
    company_name,
    website_url="",
    industry="",
    hq_location="",
) -> ResearchState:
    return {
        "job_id": job_id,
        "company_name": company_name,
        "website_url": website_url,
        "industry": industry,
        "hq_location": hq_location,
        "status": "pending",
        "documents": {},
        "curated_docs": {},
        "briefings": {},
        "final_report": "",
        "risk_scores": {},
        "competitors": [],
        "events": [],
        "errors": [],
        "created_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    from backend.state import create_initial_state

    state = create_initial_state("job_001", "Tesla")
    print("✅ State created")
    print("Fields:", list(state.keys()))
    assert state["job_id"] == "job_001"
    assert state["company_name"] == "Tesla"
    assert state["documents"] == {}
    assert state["errors"] == []
    assert state["status"] == "pending"
    print("✅ All assertions passed")
