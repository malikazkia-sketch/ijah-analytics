"""API FastAPI - POST /api/v1/prioritize (sesuai kontrak LKP P6)."""
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from prioritizer import get_model, MODEL_VERSION, DISCLAIMER, COMPONENTS

app = FastAPI(title="IJAH Analytics - AI Experiment Prioritization", version=MODEL_VERSION)


class Candidate(BaseModel):
    compound_id: str
    protein_id: str
    confidence_score: float = Field(ge=0, le=1)
    source_count: int = Field(ge=0)
    interaction_count: float = Field(ge=0)
    nims_synergy_score: float = Field(ge=0, le=1)


class Request(BaseModel):
    top_k: Optional[int] = Field(default=10, ge=1, le=500)
    candidates: List[Candidate] = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.post("/api/v1/prioritize")
def prioritize(req: Request):
    df = pd.DataFrame([c.model_dump() for c in req.candidates])
    res = get_model().run(df, top_k=req.top_k)
    results = []
    for _, r in res.iterrows():
        results.append({
            "rank": int(r["rank"]), "compound_id": r["compound_id"], "protein_id": r["protein_id"],
            "priority_score": float(r["priority_score"]), "priority_label": r["priority_label"],
            "components": {c: float(r[c]) for c in COMPONENTS},
            "cluster_id": int(r["cluster_id"]), "cluster_label": r["cluster_label"],
            "explanation": r["explanation"],
        })
    summary = get_model().cluster_summary().reset_index().to_dict(orient="records")
    return {"model_version": MODEL_VERSION, "results": results,
            "cluster_summary": summary, "disclaimer": DISCLAIMER}
