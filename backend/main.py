from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, Response
from contextlib import asynccontextmanager
from pydantic import BaseModel
from uuid import uuid4
import asyncio
from pathlib import Path
from fpdf import FPDF

from backend.state import create_initial_state
from backend.graph import app as graph_app
from backend.events import event_manager
from backend.db.sqlite import init_db, save_job, get_history


@asynccontextmanager
async def lifespan(app):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(title="PrismIntel API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store for active/recent jobs
jobs = {}


class ResearchRequest(BaseModel):
    """Request body for starting a research pipeline."""
    company_name: str
    website_url: str = ""
    hq_location: str = ""
    industry: str = ""


async def run_pipeline(job_id: str, state: dict):
    """Execute the LangGraph pipeline in the background."""
    try:
        await event_manager.publish(job_id, "progress",
                                    {"message": "Pipeline starting...", "pct": 5})
        result = await graph_app.ainvoke(state)
        jobs[job_id] = {**result, "status": "complete"}
        save_job(job_id, state["company_name"],
                 "complete", result["final_report"])
        await event_manager.publish(job_id, "risk_score",
                                    {"scores": result.get("risk_scores", {})})
        await event_manager.publish(job_id, "competitors_done",
                                    {"competitors": result.get("competitors", [])})
        await event_manager.publish(job_id, "complete",
                                    {"report": result["final_report"]})
    except Exception as e:
        jobs[job_id]["status"] = "error"
        await event_manager.publish(job_id, "error",
                                    {"message": str(e)})


@app.post("/research", status_code=202)
async def start_research(req: ResearchRequest):
    """Start a new research pipeline. Returns job_id immediately."""
    job_id = str(uuid4())
    state = create_initial_state(
        job_id=job_id,
        company_name=req.company_name,
        website_url=req.website_url,
        industry=req.industry,
        hq_location=req.hq_location,
    )
    jobs[job_id] = {**state, "status": "running"}
    save_job(job_id, req.company_name, "running")
    event_manager.create_queue(job_id)
    asyncio.create_task(run_pipeline(job_id, state))
    return {"job_id": job_id, "status": "started"}


@app.get("/research/{job_id}/report")
async def get_report(job_id: str):
    """Return the report for a completed job, or current status."""
    if job_id not in jobs:
        return {"status": "not_found"}
    job = jobs[job_id]
    if job["status"] == "complete":
        return {"status": "complete",
                "report": job.get("final_report", "")}
    return {"status": job["status"]}


@app.get("/history")
async def history():
    """Return last 10 research jobs from SQLite."""
    return {"history": get_history()}


@app.get("/research/{job_id}/stream")
async def stream_research(job_id: str):
    """SSE stream endpoint — streams real-time research events."""
    return StreamingResponse(
        event_manager.stream(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.post("/generate-pdf")
async def generate_pdf(body: dict):
    """Accept markdown string, return PDF bytes."""
    markdown = body.get("markdown", "")
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in markdown.split("\n"):
        clean = (line.replace("### ", "").replace("## ", "")
                     .replace("# ", "").replace("**", "")
                     .replace("*", "").replace("`", "").strip())
        if not clean:
            pdf.ln(3)
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
        else:
            pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(pdf.epw, 7, clean, new_x="LMARGIN", new_y="NEXT")
    pdf_bytes = pdf.output()
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition":
                 "attachment; filename=prismintel_report.pdf"}
    )


# --- Static files: serve frontend (must be LAST, after all routes) ---
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir),
          html=True), name="frontend")
