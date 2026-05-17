from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from myca_recsys.config import load_settings

API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    settings = load_settings()
    if not settings.api_key:
        return
    if api_key == settings.api_key:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Missing or invalid {API_KEY_HEADER_NAME}",
    )
