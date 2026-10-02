"""Small helper for calling the CoinMarketCap API."""

import os

import httpx

BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapError(Exception):
    """Raised when CoinMarketCap cannot be reached or returns an error."""


def get_api_key() -> str:
    api_key = os.getenv("CMC_API_KEY", "").strip()
    if not api_key:
        raise CoinMarketCapError("CMC_API_KEY is not set. Add it to your .env file.")
    return api_key


async def cmc_get(endpoint: str, params: dict | None = None, transport=None) -> dict:
    """Send a GET request to CoinMarketCap and return the JSON response.

    `transport` is only used by tests to fake the API.
    """
    headers = {"X-CMC_PRO_API_KEY": get_api_key(), "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(
            base_url=BASE_URL, headers=headers, timeout=10, transport=transport
        ) as client:
            response = await client.get(endpoint, params=params)
    except httpx.RequestError as exc:
        raise CoinMarketCapError(f"Could not reach CoinMarketCap ({type(exc).__name__}).") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise CoinMarketCapError(
            f"CoinMarketCap returned an invalid response (HTTP {response.status_code})."
        ) from exc

    status = data.get("status") if isinstance(data, dict) else None
    error_message = status.get("error_message") if isinstance(status, dict) else None

    if response.status_code != 200 or error_message:
        message = error_message or "unknown error"
        raise CoinMarketCapError(
            f"CoinMarketCap error (HTTP {response.status_code}): {message}"
        )

    return data
