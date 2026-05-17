from __future__ import annotations

import logging

from myca_recsys.catalog import load_courses
from myca_recsys.llm import (
    HuggingFacePersonaClient,
    LLMAuthError,
    LLMClientError,
    MissingTokenError,
    fallback_persona,
    metadata_for,
)
from myca_recsys.models import Course, RecommendationRequest, RecommendationResponse
from myca_recsys.safety import detect_safety
from myca_recsys.scoring import rank_courses

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(
        self,
        courses: list[Course] | None = None,
        persona_client: HuggingFacePersonaClient | None = None,
    ) -> None:
        self.courses = courses or load_courses()
        self.persona_client = persona_client or HuggingFacePersonaClient()

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        persona, llm_status, source = self._build_persona(request)
        safety = detect_safety(persona, request.chat_history)
        recommendations = rank_courses(self.courses, persona, safety, request.top_n)
        metadata = metadata_for(llm_status, self.persona_client.settings, source)
        return RecommendationResponse(
            persona=persona,
            recommendations=recommendations,
            safety=safety,
            model_metadata=metadata,
        )

    def _build_persona(self, request: RecommendationRequest):
        if request.chat_history and request.chat_history.strip():
            try:
                persona = self.persona_client.extract_persona(request.chat_history, request.profile)
                return _merge_profile(request.profile, persona), "ok", "llm"
            except MissingTokenError:
                logger.info("HF_TOKEN missing; using profile fallback")
                return fallback_persona(request.profile, request.chat_history), "skipped_missing_token", "profile"
            except LLMAuthError:
                logger.warning("Hugging Face authentication failed; using profile fallback")
                return fallback_persona(request.profile, request.chat_history), "auth_failed", "profile"
            except LLMClientError as exc:
                logger.warning("LLM persona extraction failed; using profile fallback: %s", exc)
                return fallback_persona(request.profile, request.chat_history), "fallback_error", "profile"

        return fallback_persona(request.profile), "not_used", "profile"


def _merge_profile(profile, persona):
    persona.feelings = _merge_list(profile.feelings, persona.feelings)
    persona.challenges = _merge_list(profile.challenges, persona.challenges)
    persona.goals = _merge_list(profile.goals, persona.goals)
    persona.risk_signals = _merge_list(profile.risk_signals, persona.risk_signals)
    return persona


def _merge_list(primary: list[str], secondary: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in [*primary, *secondary]:
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            merged.append(item.strip())
    return merged
