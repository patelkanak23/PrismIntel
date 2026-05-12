from backend.state import ResearchState


async def collector_node(state: ResearchState) -> dict:
    docs = state.get("documents", {})
    total = sum(len(v) for v in docs.values())
    print(f"Collector: {total} total docs across {len(docs)} categories")
    for cat, items in docs.items():
        print(f"  {cat}: {len(items)} docs")
    return {"documents": docs}
