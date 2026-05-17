from __future__ import annotations

from fastapi import FastAPI

from myca_recsys.catalog import load_courses
from myca_recsys.models import Course, RecommendationRequest, RecommendationResponse
from myca_recsys.service import RecommendationEngine

app = FastAPI(title="MYCA Recommendation API", version="1.0.0")
engine = RecommendationEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/courses", response_model=list[Course])
def get_courses() -> list[Course]:
    return load_courses()


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return engine.recommend(request)
