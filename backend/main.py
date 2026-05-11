from fastapi import FastAPI


app = FastAPI(title="PrismIntel API")


@app.post("/research")
async def create_research():
    return None


@app.get("/research/{job_id}/stream")
async def stream_research(job_id):
    return None


@app.get("/research/{job_id}/report")
async def get_report(job_id):
    return None


@app.get("/history")
async def get_history():
    return None


@app.post("/generate-pdf")
async def generate_pdf():
    return None
