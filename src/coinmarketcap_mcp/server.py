"""MCP server with CoinMarketCap crypto and DEX tools."""

from dotenv import load_dotenv
from fastmcp import FastMCP

from coinmarketcap_mcp.client import CoinMarketCapError, cmc_get, get_api_key

load_dotenv()

mcp = FastMCP(
    name="CoinMarketCap MCP Server",
    instructions="Provides live crypto prices, top listings, and DEX data from CoinMarketCap.",
)


def round_or_none(value, digits: int = 2):
    """Round a number, but keep missing values as None instead of turning them into 0."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(value, digits)
    return None


def clean_code(value: str, name: str) -> str:
    """Clean up a symbol or currency code like ' btc ' -> 'BTC'."""
    value = value.strip().upper()
    if not value.isalnum() or len(value) > 15:
        raise ValueError(f"{name} must be letters/numbers only, e.g. BTC or USD.")
    return value


@mcp.tool()
async def get_latest_listings(limit: int = 10) -> dict:
    """Get the top cryptocurrencies ranked by market cap (max 50)."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50.")

    data = await cmc_get(
        "/cryptocurrency/listings/latest",
        {"limit": limit, "convert": "USD", "sort": "market_cap"},
    )

    listings = []
    for coin in data.get("data", []):
        usd = coin.get("quote", {}).get("USD", {})
        listings.append(
            {
                "rank": coin.get("cmc_rank"),
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "price_usd": round_or_none(usd.get("price"), 6),
                "market_cap_usd": round_or_none(usd.get("market_cap")),
                "volume_24h_usd": round_or_none(usd.get("volume_24h")),
                "percent_change_24h": round_or_none(usd.get("percent_change_24h")),
                "percent_change_7d": round_or_none(usd.get("percent_change_7d")),
                "date_added": coin.get("date_added"),
            }
        )

    return {"total_returned": len(listings), "listings": listings}


@mcp.tool()
async def get_crypto_price(symbol: str, convert: str = "USD") -> dict:
    """Get the current price and market data for one cryptocurrency, e.g. BTC."""
    symbol = clean_code(symbol, "symbol")
    convert = clean_code(convert, "convert")

    data = await cmc_get(
        "/cryptocurrency/quotes/latest", {"symbol": symbol, "convert": convert}
    )

    coin = data.get("data", {}).get(symbol)
    if not coin:
        raise CoinMarketCapError(f"No data found for symbol '{symbol}'.")

    quote = coin.get("quote", {}).get(convert, {})
    return {
        "name": coin.get("name"),
        "symbol": coin.get("symbol"),
        "price": round_or_none(quote.get("price"), 6),
        "currency": convert,
        "market_cap": round_or_none(quote.get("market_cap")),
        "percent_change_24h": round_or_none(quote.get("percent_change_24h")),
        "percent_change_7d": round_or_none(quote.get("percent_change_7d")),
        "last_updated": quote.get("last_updated"),
    }


@mcp.tool()
async def dex_transaction(platform: str, address: str, limit: int = 5) -> list:
    """Get recent DEX swap transactions for a token address on a platform."""
    if not platform.strip() or not address.strip():
        raise ValueError("platform and address are required.")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    data = await cmc_get(
        "/dex/tokens/transactions",
        {"platform": platform.strip(), "address": address.strip(), "limit": limit},
    )

    # The swaps may be inside data["data"]["swaps"] or directly in data["data"].
    result = data.get("data") or {}
    swaps = result.get("swaps", []) if isinstance(result, dict) else result

    transactions = []
    for swap in swaps:
        transactions.append(
            {
                "type": swap.get("tp"),
                "dex": swap.get("en"),
                "from_token": {
                    "symbol": swap.get("t0s"),
                    "amount": swap.get("a0"),
                    "price_in_usd": swap.get("t0pu"),
                },
                "to_token": {
                    "symbol": swap.get("t1s"),
                    "amount": swap.get("a1"),
                    "price_in_usd": swap.get("t1pu"),
                },
                "volume_usd": swap.get("v"),
            }
        )

    return transactions


@mcp.tool()
async def list_dex_platforms() -> list:
    """List all DEX platforms/networks supported by CoinMarketCap."""
    data = await cmc_get("/dex/platform/list")
    return [
        {"platform_name": platform.get("n"), "platform_id": platform.get("id")}
        for platform in data.get("data", [])
    ]


@mcp.tool()
async def get_dex_platform_detail(platform_name: str) -> dict:
    """Get details for one DEX platform. Use a name from list_dex_platforms."""
    if not platform_name.strip():
        raise ValueError("platform_name is required.")

    data = await cmc_get("/dex/platform/detail", {"platformName": platform_name.strip()})

    platform = data.get("data") or {}
    return {
        "platform_name": platform.get("n"),
        "chain_id": platform.get("chId"),
        "supported_dex_count": platform.get("dn"),
        "platform_acronym": platform.get("pltA"),
        "wrapped_native_token_id": platform.get("wcId"),
    }


def main() -> None:
    get_api_key()  # Stop early with a clear message if the key is missing.
    mcp.run()


if __name__ == "__main__":
    main()
