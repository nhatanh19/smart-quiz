import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from openai import RateLimitError
from pydantic import BaseModel
from starlette.requests import Request
from tenacity import wait_none

from app.core.config import Settings
from app.core.llm_client import (
    LLMClientAdapter,
    LLMConfigurationError,
    LLMRateLimitError,
)
from app.main import llm_rate_limit_error_handler


class GeneratedResponse(BaseModel):
    value: int


def _rate_limit_error() -> RateLimitError:
    request = httpx.Request("POST", "https://example.test/chat/completions")
    response = httpx.Response(429, request=request)
    return RateLimitError("Rate limited", response=response, body=None)


class LLMClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.adapter = LLMClientAdapter(api_key="test-key")
        self.create = AsyncMock()
        self.adapter.client = MagicMock()
        self.adapter.client.chat.completions.create = self.create

    @contextmanager
    def _without_retry_wait(self):
        retrying = self.adapter._generate_with_retry.retry
        original_wait = retrying.wait
        retrying.wait = wait_none()
        try:
            yield
        finally:
            retrying.wait = original_wait

    async def test_generate_structured_json_validates_provider_response(self) -> None:
        self.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"value": 7}')
                )
            ]
        )

        result = await self.adapter.generate_structured_json(
            "Return a value.", "value is seven", GeneratedResponse
        )

        self.assertEqual(result, GeneratedResponse(value=7))
        self.create.assert_awaited_once()
        self.assertEqual(self.create.await_args.kwargs["model"], self.adapter.model_name)
        self.assertEqual(
            self.create.await_args.kwargs["response_format"], {"type": "json_object"}
        )

    async def test_rate_limit_retries_then_succeeds(self) -> None:
        self.create.side_effect = [
            _rate_limit_error(),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"value": 3}')
                    )
                ]
            ),
        ]

        with self._without_retry_wait():
            result = await self.adapter.generate_structured_json(
                "Return a value.", "value is three", GeneratedResponse
            )

        self.assertEqual(result.value, 3)
        self.assertEqual(self.create.await_count, 2)

    async def test_rate_limit_after_three_attempts_returns_friendly_error(self) -> None:
        self.create.side_effect = [_rate_limit_error()] * 3

        with self._without_retry_wait():
            with self.assertRaisesRegex(LLMRateLimitError, "temporarily busy"):
                await self.adapter.generate_structured_json(
                    "Return a value.", "any value", GeneratedResponse
                )

        self.assertEqual(self.create.await_count, 3)

    async def test_rate_limit_http_handler_returns_friendly_503(self) -> None:
        request = Request(
            {"type": "http", "method": "POST", "path": "/", "headers": []}
        )

        response = await llm_rate_limit_error_handler(
            request,
            LLMRateLimitError(
                "The AI service is temporarily busy. Please try again later."
            ),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.body,
            b'{"success":false,"error":"The AI service is temporarily busy. Please try again later."}',
        )

    async def test_missing_api_key_fails_before_making_a_request(self) -> None:
        adapter = LLMClientAdapter(api_key="")

        with self.assertRaisesRegex(LLMConfigurationError, "not configured"):
            await adapter.generate_structured_json(
                "Return a value.", "any value", GeneratedResponse
            )

    def test_defaults_prefer_gemini_and_use_fifteen_second_timeout(self) -> None:
        settings = Settings(_env_file=None)

        self.assertEqual(
            settings.LLM_BASE_URL,
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self.assertEqual(settings.LLM_MODEL_NAME, "gemini-2.5-flash")
        self.assertEqual(settings.LLM_TIMEOUT_SECONDS, 15.0)
        self.assertEqual(settings.AI_TUTOR_TIMEOUT_SECONDS, 15.0)
        self.assertEqual(settings.AI_TUTOR_MODEL_TIMEOUT_SECONDS, 12.0)

    async def test_model_name_override_passes_through_to_completion_call(self) -> None:
        self.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"value": 9}')
                )
            ]
        )

        result = await self.adapter.generate_structured_json(
            "System", "User", GeneratedResponse, model_name="backup-fast-model"
        )

        self.assertEqual(result, GeneratedResponse(value=9))
        self.assertEqual(self.create.await_args.kwargs["model"], "backup-fast-model")

    def test_database_url_normalizes_legacy_postgres_scheme(self) -> None:
        for raw_url in (
            "postgres://user:pass@host:5432/smart_quiz",
            "postgresql://user:pass@host:5432/smart_quiz",
        ):
            cfg = Settings(_env_file=None, DATABASE_URL=raw_url)
            self.assertEqual(
                cfg.DATABASE_URL,
                "postgresql+psycopg2://user:pass@host:5432/smart_quiz",
            )

        sqlite_settings = Settings(_env_file=None, DATABASE_URL="sqlite://")
        self.assertEqual(sqlite_settings.DATABASE_URL, "sqlite://")

    def test_client_uses_environment_key_and_configured_timeout(self) -> None:
        with patch("app.core.llm_client.AsyncOpenAI") as openai_client:
            adapter = LLMClientAdapter(
                api_key="env-key",
                base_url="https://provider.test/v1",
                timeout_seconds=15,
            )
            adapter._get_client()

        openai_client.assert_called_once_with(
            api_key="env-key",
            base_url="https://provider.test/v1",
            timeout=15,
        )


if __name__ == "__main__":
    unittest.main()
