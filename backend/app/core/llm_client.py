import json
import logging
from typing import Optional, Type, TypeVar
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured."""


class LLMRateLimitError(RuntimeError):
    """Raised when the provider remains rate-limited after retries."""


class LLMResponseError(RuntimeError):
    """Raised when the provider returns no usable response."""


def _is_retryable_status_error(error: BaseException) -> bool:
    return isinstance(error, APIStatusError) and (
        error.status_code in (408, 409) or error.status_code >= 500
    )


class LLMClientAdapter:
    """Adapter for interacting with OpenAI-compatible LLM providers.

    Supports custom base URLs (Gemini OpenAI endpoint, Ollama, LocalAI, vLLM, etc.)
    and enforces strict JSON Schema output validation via Pydantic models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.api_key = settings.LLM_API_KEY if api_key is None else api_key
        self.base_url = settings.LLM_BASE_URL if base_url is None else base_url
        self.model_name = settings.LLM_MODEL_NAME if model_name is None else model_name
        self.timeout = (
            settings.LLM_TIMEOUT_SECONDS
            if timeout_seconds is None
            else timeout_seconds
        )
        if self.timeout <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise LLMConfigurationError(
                "The AI service is not configured. Please contact support."
            )
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self.client

    async def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.2,
        model_name: Optional[str] = None,
    ) -> T:
        """Call an LLM provider and validate its JSON response with a Pydantic model."""
        self._get_client()
        try:
            return await self._generate_with_retry(
                system_prompt, user_prompt, response_schema, temperature, model_name
            )
        except RateLimitError as error:
            logger.error("LLM provider remained rate-limited after three attempts")
            raise LLMRateLimitError(
                "The AI service is temporarily busy. Please try again later."
            ) from error

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=(
            retry_if_exception_type((APIConnectionError, RateLimitError))
            | retry_if_exception(_is_retryable_status_error)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.2,
        model_name: Optional[str] = None,
    ) -> T:
        """Request JSON and validate it, retrying only transient provider failures."""
        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        augmented_system_prompt = (
            f"{system_prompt}\n\n"
            f"IMPORTANT: You MUST respond ONLY with a valid JSON object matching this JSON Schema:\n"
            f"{schema_json}\n"
            f"Do not include markdown code fence formatting (e.g. ```json). Output pure JSON only."
        )

        try:
            response = await self._get_client().chat.completions.create(
                model=model_name or self.model_name,
                messages=[
                    {"role": "system", "content": augmented_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )

            if not response.choices:
                raise LLMResponseError("The AI service returned an empty response.")

            raw_content = response.choices[0].message.content
            if not isinstance(raw_content, str) or not raw_content.strip():
                raise LLMResponseError("The AI service returned an empty response.")
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

            validated_data = response_schema.model_validate_json(cleaned_content)
            return validated_data

        except ValidationError:
            logger.exception("LLM output validation failed")
            raise
        except APIStatusError as error:
            logger.error(
                "LLM API returned status error %s: %s",
                error.status_code,
                error.message,
            )
            raise


# Shared singleton instance configured with app settings
llm_client = LLMClientAdapter()
