from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    hf_token: str | None
    hf_api_url: str
    hf_model_id: str
    request_timeout_seconds: int
    retry_attempts: int


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    token = os.getenv("HF_TOKEN")
    return Settings(
        hf_token=_clean_token(token),
        hf_api_url=os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions"),
        hf_model_id=os.getenv("HF_MODEL_ID", "Qwen/Qwen3.5-35B-A3B"),
        request_timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "30")),
        retry_attempts=int(os.getenv("HF_RETRY_ATTEMPTS", "2")),
    )


def _clean_token(token: str | None) -> str | None:
    if not token:
        return None
    cleaned = token.strip().strip('"').strip("'")
    return cleaned or None
