import json
import logging
from typing import Optional, Type, TypeVar
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, APIStatusError
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


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
        self.api_key = api_key or settings.LLM_API_KEY or "dummy-api-key"
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model_name = model_name or settings.LLM_MODEL_NAME
        self.timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """Call LLM provider and validate response strictly against a Pydantic BaseModel.

        Args:
            system_prompt: Guiding instruction and persona for the LLM.
            user_prompt: Specific input content or request.
            response_schema: Subclass of Pydantic BaseModel defining the desired output structure.
            temperature: Creativity/randomness control (default 0.2 for strict JSON).

        Returns:
            An instance of response_schema populated with the LLM output.

        Raises:
            ValidationError: If LLM output fails schema validation.
            APIStatusError: If LLM API returns an unrecoverable HTTP status.
        """
        # Append schema description to system prompt for models that need explicit schema cues
        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        augmented_system_prompt = (
            f"{system_prompt}\n\n"
            f"IMPORTANT: You MUST respond ONLY with a valid JSON object matching this JSON Schema:\n"
            f"{schema_json}\n"
            f"Do not include markdown code fence formatting (e.g. ```json). Output pure JSON only."
        )

        try:
            # First attempt structured parsing using client.beta.chat.completions.parse if supported
            try:
                completion = await self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": augmented_system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=response_schema,
                    temperature=temperature,
                )
                if completion.choices and completion.choices[0].message.parsed:
                    return completion.choices[0].message.parsed
            except Exception as parse_error:
                logger.debug(
                    "Standard beta parse not supported by host (%s), falling back to json_object: %s",
                    self.base_url,
                    parse_error,
                )

            # Fallback to standard chat completions with json_object format
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": augmented_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )

            raw_content = response.choices[0].message.content or "{}"
            # Clean possible markdown wrapping if returned despite instructions
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

        except ValidationError as ve:
            logger.error("LLM output validation failed: %s", ve)
            raise ve
        except APIStatusError as se:
            logger.error("LLM API returned status error %s: %s", se.status_code, se.message)
            raise se
        except Exception as e:
            logger.error("Unexpected error in LLMClientAdapter: %s", e)
            raise e


# Shared singleton instance configured with app settings
llm_client = LLMClientAdapter()
