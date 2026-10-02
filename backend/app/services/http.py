import httpx

from app.config import get_settings

_client: httpx.AsyncClient | None = None


class ExternalAPIError(Exception):
    """An external provider failed; `reason` is safe to show to users."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def get_http() -> httpx.AsyncClient:
    """Shared pooled client for outbound API calls (FastAPI dependency; overridden in tests)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=get_settings().http_timeout_seconds)
    return _client


async def request_json(client: httpx.AsyncClient, method: str, url: str, provider: str, **kwargs) -> dict:
    try:
        r = await client.request(method, url, **kwargs)
    except httpx.TimeoutException:
        raise ExternalAPIError(f"{provider} timed out") from None
    except httpx.HTTPError:
        raise ExternalAPIError(f"{provider} is unreachable") from None
    if r.status_code in (401, 403):
        raise ExternalAPIError(f"{provider} rejected the API key")
    if r.status_code == 429:
        raise ExternalAPIError(f"{provider} rate limit reached")
    if r.status_code == 404:
        raise ExternalAPIError(f"{provider} has no data for this location")
    if r.status_code >= 400:
        raise ExternalAPIError(f"{provider} returned an error ({r.status_code})")
    try:
        return r.json()
    except ValueError:
        raise ExternalAPIError(f"{provider} returned an invalid response") from None
