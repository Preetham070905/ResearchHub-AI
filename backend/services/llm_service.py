"""
Async LLM Service using Groq for ResearchHub AI.

FEATURES:
1. ASYNC: Uses asyncio.to_thread() so FastAPI can handle other requests
   while waiting for Groq.
2. RETRY: Retries 5x with smart backoff. For 429 rate-limit errors,
   parses the server's suggested wait time (capped at 120s).
3. FLEXIBLE: Each agent can request different max_tokens.
4. THROTTLED: Global semaphore limits concurrent API calls to avoid
   exhausting Groq's rate limits (especially on free tier).
"""

import asyncio
import time as _time
import re
import logging
from groq import Groq
from config import settings

logger = logging.getLogger(__name__)

# Initialize Groq client once (reused across all calls)
_client = Groq(api_key=settings.GROQ_API_KEY)

# Global semaphore: limits how many LLM calls run concurrently.
# Groq free tier allows ~30 req/min for llama-3.3-70b-versatile.
# With 3 concurrent calls + 0.5s delay, we stay safely under the limit.
_concurrency = settings.LLM_CONCURRENCY
_semaphore = asyncio.Semaphore(_concurrency)

# Minimum delay between consecutive LLM calls (seconds).
# Prevents burst requests that trigger Groq's per-second rate limit.
_MIN_CALL_DELAY = 0.5
_last_call_time = 0.0
_delay_lock = asyncio.Lock()


def _sync_call(messages: list, max_tokens: int = None) -> str:
    """Synchronous Groq API call (runs inside thread pool)."""
    response = _client.chat.completions.create(
        messages=messages,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
    )
    return response.choices[0].message.content


def _parse_retry_after(error_msg: str) -> float | None:
    """Extract wait time in seconds from Groq rate-limit error message."""
    match = re.search(r"Please try again in (\d+(?:\.\d+)?)m(\d+(?:\.\d+)?)s", str(error_msg))
    if match:
        return float(match.group(1)) * 60 + float(match.group(2))
    match = re.search(r"Please try again in (\d+(?:\.\d+)?)s", str(error_msg))
    if match:
        return float(match.group(1))
    return None


async def call_llm_async(
    messages: list,
    max_tokens: int = None,
    retries: int = 5,
    backoff_base: float = 2.0
) -> str:
    """
    Async LLM call with exponential backoff retry and concurrency throttling.

    The global semaphore ensures at most 1 call runs at a time (configurable).
    A minimum delay between calls prevents burst rate-limit hits.

    Args:
        messages: Chat messages list (system + user)
        max_tokens: Override default max tokens for this call
        retries: Number of retry attempts (default 5)
        backoff_base: Base delay in seconds (doubles each retry)

    Returns:
        LLM response text

    Raises:
        RuntimeError: If all retries are exhausted
    """
    if not messages:
        raise ValueError("messages cannot be empty")

    MAX_RATE_LIMIT_WAIT = 120  # never wait more than 2 minutes per retry

    last_error = None

    async with _semaphore:
        # Enforce minimum delay between calls to spread out requests
        global _last_call_time
        async with _delay_lock:
            now = _time.time()
            elapsed = now - _last_call_time
            if elapsed < _MIN_CALL_DELAY:
                await asyncio.sleep(_MIN_CALL_DELAY - elapsed)
            _last_call_time = _time.time()

        for attempt in range(retries):
            try:
                result = await asyncio.to_thread(_sync_call, messages, max_tokens)

                # Auto-strip markdown JSON block if present
                result = result.strip()
                if result.startswith("```"):
                    lines = result.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    result = "\n".join(lines).strip()

                return result

            except Exception as e:
                last_error = e
                error_str = str(e)

                if "429" in error_str or "rate_limit" in error_str.lower():
                    retry_after = _parse_retry_after(error_str)
                    if retry_after is not None:
                        wait_time = min(retry_after + 1, MAX_RATE_LIMIT_WAIT)
                    else:
                        wait_time = min(backoff_base * (2 ** attempt), MAX_RATE_LIMIT_WAIT)
                else:
                    wait_time = backoff_base * (2 ** attempt)

                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )

                if attempt < retries - 1:
                    await asyncio.sleep(wait_time)

    raise RuntimeError(
        f"LLM call failed after {retries} attempts. Last error: {last_error}"
    )
