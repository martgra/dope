"""Retry configuration for HTTP clients used with LLM providers."""

import httpx2
from pydantic_ai.retries import (
    AsyncHTTPX2TenacityTransport,
    RetryConfig,
    wait_retry_after,
)
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dope.core.loop_cache import loop_scoped_cache


def _should_retry_status(response: httpx2.Response) -> None:
    """Raise exceptions for retryable HTTP status codes.

    Args:
        response: The HTTP response to validate.

    Raises:
        httpx2.HTTPStatusError: For 429 (rate limit) and 5xx (server errors).
    """
    if response.status_code in (429, 502, 503, 504):
        response.raise_for_status()


@loop_scoped_cache
def get_retry_client() -> httpx2.AsyncClient:
    """Create an httpx2.AsyncClient with smart retry handling.

    Migrated from ``httpx``/``AsyncTenacityTransport`` to
    ``httpx2``/``AsyncHTTPX2TenacityTransport`` per pydantic-ai's
    deprecation notice (both the old client and the old transport are
    slated for removal in pydantic-ai v3). httpx2 is a wire-compatible
    fork used internally by pydantic-ai's providers; behavior of the
    retry policy below is unchanged.

    Configured to handle:
    - Connection errors (network issues)
    - Timeout errors
    - Rate limiting (429) with Retry-After header support
    - Server errors (5xx)

    The client will retry up to 5 times with exponential backoff
    starting at 1 second and maxing out at 60 seconds. It respects
    Retry-After headers for intelligent rate limit handling.

    Returns:
        httpx2.AsyncClient: Configured client with retry logic.
    """
    transport = AsyncHTTPX2TenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors and connection/timeout issues
            retry=retry_if_exception_type(
                (
                    httpx2.HTTPStatusError,
                    httpx2.ConnectError,
                    httpx2.TimeoutException,
                    httpx2.ReadError,
                    httpx2.RemoteProtocolError,
                    httpx2.PoolTimeout,
                    httpx2.NetworkError,
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
    return httpx2.AsyncClient(transport=transport, timeout=30.0)
