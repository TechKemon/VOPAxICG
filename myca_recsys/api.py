from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from myca_recsys.auth import require_api_key
from myca_recsys.catalog import load_courses
from myca_recsys.models import Course, RecommendationRequest, RecommendationResponse
from myca_recsys.service import RecommendationEngine

tags_metadata = [
    {
        "name": "System",
        "description": "Health and browser-friendly entrypoints.",
    },
    {
        "name": "Courses",
        "description": "Inspect the MYCA course catalog used by the recommender.",
    },
    {
        "name": "Recommendations",
        "description": "Generate ranked MYCA course recommendations from a user profile.",
    },
]

app = FastAPI(
    title="MYCA Recommendation API",
    version="1.0.0",
    description=(
        "Interactive API docs for the MYCA hybrid recommendation system. "
        "Use the Authorize button with the API key from `MYCA_API_KEY` when auth is enabled."
    ),
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },
)
engine = RecommendationEngine()


@app.get("/", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"], summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/v1/courses",
    response_model=list[Course],
    tags=["Courses"],
    summary="List MYCA courses",
    dependencies=[Depends(require_api_key)],
)
def get_courses() -> list[Course]:
    return load_courses()


@app.post(
    "/v1/recommendations",
    response_model=RecommendationResponse,
    tags=["Recommendations"],
    summary="Recommend courses for a MYCA user",
    description=(
        "Accepts a structured profile and optional chat history. The LLM may enrich the persona, "
        "but deterministic scoring owns the final course ranking."
    ),
    dependencies=[Depends(require_api_key)],
)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return engine.recommend(request)
