import httpx
import pytest

from coinmarketcap_mcp.client import CoinMarketCapError, cmc_get


@pytest.fixture(autouse=True)
def fake_api_key(monkeypatch):
    monkeypatch.setenv("CMC_API_KEY", "test-key")


def fake_api(status_code, json_body):
    """Return a fake transport that always answers with the given response."""
    return httpx.MockTransport(lambda request: httpx.Response(status_code, json=json_body))


async def test_returns_json_and_sends_api_key():
    def handler(request):
        assert request.headers["X-CMC_PRO_API_KEY"] == "test-key"
        return httpx.Response(200, json={"data": {"BTC": {"name": "Bitcoin"}}})

    data = await cmc_get("/test", transport=httpx.MockTransport(handler))
    assert data["data"]["BTC"]["name"] == "Bitcoin"


async def test_raises_on_api_error_message():
    transport = fake_api(200, {"status": {"error_code": 1002, "error_message": "bad key"}})
    with pytest.raises(CoinMarketCapError, match="bad key"):
        await cmc_get("/test", transport=transport)


async def test_raises_on_http_error():
    with pytest.raises(CoinMarketCapError, match="HTTP 429"):
        await cmc_get("/test", transport=fake_api(429, {}))


async def test_raises_on_invalid_json():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="not json"))
    with pytest.raises(CoinMarketCapError, match="invalid response"):
        await cmc_get("/test", transport=transport)


async def test_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("CMC_API_KEY")
    with pytest.raises(CoinMarketCapError, match="CMC_API_KEY"):
        await cmc_get("/test")
