import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="CoinMarketCap MCP Server",
    instructions="Provides tools to get live crypto prices and top listings from CoinMarketCap.",
)

CMC_API_KEY = "61a2ddaecbeb47398a06b704065096e8"
BASE_URL = "https://pro-api.coinmarketcap.com/v1"

HEADERS = {
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
    "Accept": "application/json",
}

@mcp.tool()
async def get_latest_listings(limit: int = 10) -> dict:
    """Get the latest cryptocurrency listings ranked by market cap."""
    limit = min(limit, 50)
    url = f"{BASE_URL}/cryptocurrency/listings/latest"
    params = {
        "limit": limit,
        "convert": "USD",
        "sort": "date_added"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

    results = []
    for coin in data.get("data", []):
        quote = coin.get("quote", {}).get("USD", {})
        results.append({
            "rank": coin["cmc_rank"],
            "name": coin["name"],
            "symbol": coin["symbol"],
            "price_usd": round(quote.get("price", 0), 4),
            "market_cap_usd": round(quote.get("market_cap", 0), 2),
            "volume_24h_usd": round(quote.get("volume_24h", 0), 2),
            "percent_change_24h": round(quote.get("percent_change_24h", 0), 2),
            "percent_change_7d": round(quote.get("percent_change_7d", 0), 2),
            "date_added": coin["date_added"]
        })

    return {"total_returned": len(results), "listings": results}


@mcp.tool()
async def get_crypto_price(symbol: str, convert: str = "USD") -> dict:
    """Get the current price and market data for a specific cryptocurrency."""
    url = f"{BASE_URL}/cryptocurrency/quotes/latest"
    params = {"symbol": symbol.upper().strip(), "convert": convert.upper().strip()}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

    coin_data = data.get("data", {}).get(symbol.upper())
    if not coin_data:
        return {"error": f"No data found for symbol '{symbol}'."}

    quote = coin_data.get("quote", {}).get(convert.upper(), {})

    return {
        "name": coin_data["name"],
        "symbol": coin_data["symbol"],
        "price": round(quote.get("price", 0), 4),
        "currency": convert.upper(),
        "market_cap": round(quote.get("market_cap", 0), 2),
        "percent_change_24h": round(quote.get("percent_change_24h", 0), 2),
        "percent_change_7d": round(quote.get("percent_change_7d", 0), 2),
        "last_updated": coin_data.get("last_updated"),
    }

@mcp.tool()
async def dex_transaction(platform: str, address: str, limit: int = 5) -> list:
    """
    Retrieve on-chain swap transactions for a DEX token.
    
    Returns a list of recent trades including price,
    amount, buyer/seller, and transaction hash.
    """
    url = f"{BASE_URL}/dex/tokens/transactions"
    params = {
        "platform": platform.strip(),
        "address": address.strip(),
        "limit": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    
    transactions = []

    for transaction in data.get("data",[]).get("swaps",[]):
        transactions.append({
            "Type": transaction["tp"],
            "DEX": transaction["en"],
            "from_token": {
                "symbol": transaction["t0s"],
                "amount": transaction["a0"],
                "price_in_usd": transaction["t1pu"]
            },
            "to_token": {
                "symbol": transaction["t1s"],
                "amount": transaction["a1"],
                "price_in_usd": transaction["t1pu"]
            },
            "total_transaction_volume_in_USD": transaction["v"]
        })

    return transactions

@mcp.tool()
async def list_dex_platforms() -> list:
    """
    Retrieve all supported DEX platforms/networks.
    
    Returns platform ID, name, and slug —
    use the ID in other DEX endpoints like meme/list or token/pools.
    """
    url = f"{BASE_URL}/dex/platform/list"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS,timeout=10)
        response.raise_for_status()
        data = response.json()
    
    platforms = []

    for platform in data.get("data",[]):
        platforms.append({
            "platform_name": platform["n"],
            "platform_id": platform["id"]
        })

    return platforms

@mcp.tool()
async def get_dex_platform_detail(pName: str) -> dict:
    """
    Retrieve detailed metadata for a specific DEX platform/network.
    
    Returns chain info, logo, website, and supported DEXs.
    Use platform ID or slug from list_dex_platforms as input.
    """
    url = f"{BASE_URL}/dex/platform/detail"
    params = {
        "platformName": pName.strip()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=HEADERS,timeout=10)
        response.raise_for_status()
        data = response.json()
    
    platform = data.get("data","{}")

    return {
        "platform_name": platform["n"],
        "Interna_ chain_ID": platform["chId"],
        "no_of_supported_dex_on_platform": platform["dn"],
        "platform acronym": platform["pltA"],
        "Wrapped_native_token_ID": platform["wcId"]
    }


if __name__ == "__main__":
    mcp.run()