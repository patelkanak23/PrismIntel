from backend.state import ResearchState


async def curator_node(state: ResearchState) -> dict:
    curated = {}
    for category, docs in state.get("documents", {}).items():
        if category == "website":
            curated[category] = docs
        else:
            filtered = [d for d in docs if d.get("score", 0) >= 0.4]
            sorted_docs = sorted(
                filtered,
                key=lambda x: x.get("score", 0),
                reverse=True,
            )
            curated[category] = sorted_docs[:20]
    total = sum(len(v) for v in curated.values())
    print(f"Curator: kept {total} docs after filtering")
    return {"curated_docs": curated}
