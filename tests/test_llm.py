import pytest
import requests

from myca_recsys.config import Settings
from myca_recsys.llm import (
    HuggingFacePersonaClient,
    LLMAuthError,
    LLMResponseError,
    MissingTokenError,
    parse_persona_response,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.text)


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.response


def settings(token="hf_test", retries=0):
    return Settings(
        hf_token=token,
        hf_api_url="https://example.test",
        hf_model_id="test-model",
        request_timeout_seconds=1,
        retry_attempts=retries,
    )


def test_parse_persona_response_accepts_markdown_json():
    persona = parse_persona_response(
        '```json\n{"summary":"Needs help","feelings":["anxious"],"challenges":["exam pressure"],"goals":["calm"]}\n```'
    )

    assert persona.summary == "Needs help"
    assert persona.feelings == ["anxious"]


def test_parse_persona_response_rejects_malformed_json():
    with pytest.raises(ValueError):
        parse_persona_response("{bad json")


def test_client_raises_missing_token_before_calling_api():
    client = HuggingFacePersonaClient(settings=settings(token=None), session=FakeSession())

    with pytest.raises(MissingTokenError):
        client.extract_persona("hello")


def test_client_raises_auth_error_on_401():
    client = HuggingFacePersonaClient(settings=settings(), session=FakeSession(FakeResponse(status_code=401)))

    with pytest.raises(LLMAuthError):
        client.extract_persona("hello")


def test_client_raises_response_error_after_timeout():
    client = HuggingFacePersonaClient(settings=settings(retries=0), session=FakeSession(exc=requests.Timeout()))

    with pytest.raises(LLMResponseError):
        client.extract_persona("hello")


def test_client_does_not_retry_dns_resolution_errors():
    session = FakeSession(
        exc=requests.ConnectionError(
            "NameResolutionError: Failed to resolve 'router.huggingface.co' "
            "([Errno 8] nodename nor servname provided, or not known)"
        )
    )
    client = HuggingFacePersonaClient(settings=settings(retries=3), session=session)

    with pytest.raises(LLMResponseError):
        client.extract_persona("hello")

    assert session.calls == 1
