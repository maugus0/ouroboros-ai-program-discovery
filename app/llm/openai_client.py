"""OpenAI API client with retry logic."""

import json

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """Return a lazily-initialised AsyncOpenAI client."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def call_openai(
    system_prompt: str,
    user_content: str,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    json_mode: bool = True,
) -> dict:
    """Send a chat completion request to OpenAI and return the parsed response.

    Args:
        system_prompt: The system instruction for the model.
        user_content: The user's query or content.
        model: Override the default model.
        max_tokens: Override the default max tokens.
        temperature: Override the default temperature.
        json_mode: If True, request JSON response format.

    Returns:
        Dictionary with content, model, provider, and token usage.
    """
    client = get_openai_client()
    model = model or settings.OPENAI_MODEL
    max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
    temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

    logger.info("openai_call_started", model=model)

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)

    raw = response.choices[0].message.content
    if raw is None:
        raise ValueError("OpenAI returned empty message content")
    usage = response.usage

    logger.info(
        "openai_call_completed",
        model=model,
        input_tokens=usage.prompt_tokens if usage else None,
        output_tokens=usage.completion_tokens if usage else None,
    )

    content = json.loads(raw) if json_mode else raw
    return {
        "content": content,
        "model": model,
        "provider": "openai",
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
    }
