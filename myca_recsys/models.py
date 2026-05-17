from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Course(BaseModel):
    id: str
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    stopwords: list[str] = Field(default_factory=list)
    domains: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("id", "title", "description")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class UserProfile(BaseModel):
    feelings: list[str] = Field(default_factory=list, examples=[["anxious", "overwhelmed"]])
    challenges: list[str] = Field(default_factory=list, examples=[["exam pressure", "fear of failure"]])
    goals: list[str] = Field(default_factory=list, examples=[["manage stress"]])
    risk_signals: list[str] = Field(default_factory=list, examples=[[]])

    @field_validator("feelings", "challenges", "goals", "risk_signals", mode="before")
    @classmethod
    def coerce_strings(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class Persona(UserProfile):
    summary: str = ""


class RecommendationRequest(BaseModel):
    profile: UserProfile = Field(default_factory=UserProfile)
    chat_history: str | None = Field(
        default=None,
        examples=["I am scared about exams and keep comparing myself with classmates."],
    )
    top_n: int = Field(default=3, ge=1, le=20)

    @model_validator(mode="after")
    def require_some_signal(self) -> "RecommendationRequest":
        has_profile = any(
            [
                self.profile.feelings,
                self.profile.challenges,
                self.profile.goals,
                self.profile.risk_signals,
            ]
        )
        if not has_profile and not (self.chat_history and self.chat_history.strip()):
            raise ValueError("profile or chat_history is required")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile": {
                    "feelings": ["anxious"],
                    "challenges": ["exam pressure", "fear of failure"],
                    "goals": ["manage stress"],
                    "risk_signals": [],
                },
                "chat_history": "I am scared about exams and marks.",
                "top_n": 3,
            }
        }
    )


class ScoreBreakdown(BaseModel):
    keyword_matches: int = 0
    domain_matches: int = 0
    text_matches: int = 0
    stopword_penalty: float = 0.0
    crisis_boost: float = 0.0


class RecommendationItem(BaseModel):
    id: str
    title: str
    score: float
    reason: str
    matched_signals: list[str] = Field(default_factory=list)
    scoring: ScoreBreakdown = Field(default_factory=ScoreBreakdown)


class SafetyInfo(BaseModel):
    is_crisis: bool = False
    message: str | None = None
    matched_signals: list[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    provider: str = "huggingface"
    model: str | None = None
    persona_source: str = "profile"
    llm_status: str = "not_used"


class RecommendationResponse(BaseModel):
    persona: Persona
    recommendations: list[RecommendationItem]
    safety: SafetyInfo
    model_metadata: ModelMetadata = Field(default_factory=ModelMetadata)

    model_config = ConfigDict(populate_by_name=True)
