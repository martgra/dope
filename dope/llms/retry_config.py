"""Retry configuration for HTTP clients used with LLM providers."""

from functools import lru_cache

import httpx
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def _should_retry_status(response: httpx.Response) -> None:
    """Raise exceptions for retryable HTTP status codes.

    Args:
        response: The HTTP response to validate.

    Raises:
        httpx.HTTPStatusError: For 429 (rate limit) and 5xx (server errors).
    """
    if response.status_code in (429, 502, 503, 504):
        response.raise_for_status()


@lru_cache(maxsize=1)
def get_retry_client() -> httpx.AsyncClient:
    """Create an httpx.AsyncClient with smart retry handling.

    Configured to handle:
    - Connection errors (network issues)
    - Timeout errors
    - Rate limiting (429) with Retry-After header support
    - Server errors (5xx)

    The client will retry up to 5 times with exponential backoff
    starting at 1 second and maxing out at 60 seconds. It respects
    Retry-After headers for intelligent rate limit handling.

    Returns:
        httpx.AsyncClient: Configured client with retry logic.
    """
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors and connection/timeout issues
            retry=retry_if_exception_type(
                (
                    httpx.HTTPStatusError,
                    httpx.ConnectError,
                    httpx.TimeoutException,
                    httpx.ReadError,
                    httpx.RemoteProtocolError,
                    httpx.PoolTimeout,
                    httpx.NetworkError,
                )
            ),
            # Smart waiting: respects Retry-After headers, falls back to exponential backoff
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, min=1, max=60),
                max_wait=300,  # Don't wait more than 5 minutes
            ),
            # Stop after 5 attempts
            stop=stop_after_attempt(5),
            # Re-raise the last exception if all retries fail
            reraise=True,
        ),
        validate_response=_should_retry_status,
    )
    return httpx.AsyncClient(transport=transport, timeout=30.0)
