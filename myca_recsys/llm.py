from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from myca_recsys.config import Settings, load_settings
from myca_recsys.models import ModelMetadata, Persona, UserProfile

logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    pass


class MissingTokenError(LLMClientError):
    pass


class LLMAuthError(LLMClientError):
    pass


class LLMResponseError(LLMClientError):
    pass


class HuggingFacePersonaClient:
    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None) -> None:
        self.settings = settings or load_settings()
        self.session = session or requests.Session()

    def extract_persona(self, chat_history: str, profile: UserProfile | None = None) -> Persona:
        if not self.settings.hf_token:
            raise MissingTokenError("HF_TOKEN is missing")

        payload = self._payload(chat_history, profile or UserProfile())
        headers = {
            "Authorization": f"Bearer {self.settings.hf_token}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.settings.retry_attempts + 2):
            try:
                response = self.session.post(
                    self.settings.hf_api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.settings.request_timeout_seconds,
                )
                if response.status_code == 401:
                    raise LLMAuthError("Hugging Face authentication failed")
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return parse_persona_response(content)
            except LLMAuthError:
                raise
            except requests.ConnectionError as exc:
                last_error = exc
                logger.warning("persona extraction connection failed: %s", exc)
                if _is_dns_resolution_error(exc):
                    break
                if attempt <= self.settings.retry_attempts:
                    time.sleep(0.25 * attempt)
            except (requests.Timeout, requests.HTTPError, KeyError, json.JSONDecodeError, LLMResponseError) as exc:
                last_error = exc
                logger.warning("persona extraction attempt %s failed: %s", attempt, exc)
                if attempt <= self.settings.retry_attempts:
                    time.sleep(0.25 * attempt)

        raise LLMResponseError(f"persona extraction failed: {last_error}")

    def _payload(self, chat_history: str, profile: UserProfile) -> dict[str, Any]:
        system_prompt = (
            "You extract a MYCA mental-health learning persona. Return only JSON with "
            "summary, feelings, challenges, goals, and risk_signals. Do not rank courses."
        )
        user_prompt = {
            "profile": profile.model_dump(),
            "chat_history": chat_history,
        }
        return {
            "model": self.settings.hf_model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ],
            "max_tokens": 600,
            "temperature": 0.1,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object"},
            "stream": False,
        }


def parse_persona_response(content: str) -> Persona:
    clean = _strip_markdown_json(content)
    raw = json.loads(clean)
    if "generated_persona" in raw:
        raw = raw["generated_persona"]
    persona = Persona(
        summary=str(raw.get("summary", "")).strip(),
        feelings=raw.get("feelings", raw.get("expressed_feelings", [])),
        challenges=raw.get("challenges", raw.get("reported_challenges", [])),
        goals=raw.get("goals", raw.get("expressed_goals", [])),
        risk_signals=raw.get("risk_signals", []),
    )
    if not any([persona.summary, persona.feelings, persona.challenges, persona.goals, persona.risk_signals]):
        raise LLMResponseError("persona response was empty")
    return persona


def fallback_persona(profile: UserProfile, chat_history: str | None = None) -> Persona:
    summary = "Profile-based recommendation"
    if chat_history:
        summary = _summarize_chat(chat_history)
    return Persona(
        summary=summary,
        feelings=profile.feelings,
        challenges=profile.challenges,
        goals=profile.goals,
        risk_signals=profile.risk_signals,
    )


def metadata_for(status: str, settings: Settings | None = None, source: str = "profile") -> ModelMetadata:
    loaded = settings or load_settings()
    return ModelMetadata(model=loaded.hf_model_id, persona_source=source, llm_status=status)


def _strip_markdown_json(content: str) -> str:
    text = content.strip()
    if text.startswith("```json"):
        return text.split("```json", 1)[1].split("```", 1)[0].strip()
    if text.startswith("```"):
        return text.split("```", 1)[1].split("```", 1)[0].strip()
    return text


def _summarize_chat(chat_history: str) -> str:
    text = " ".join(chat_history.split())
    if len(text) <= 180:
        return text
    return f"{text[:177]}..."


def _is_dns_resolution_error(exc: requests.ConnectionError) -> bool:
    message = str(exc).lower()
    return "nameresolutionerror" in message or "failed to resolve" in message or "nodename nor servname" in message
