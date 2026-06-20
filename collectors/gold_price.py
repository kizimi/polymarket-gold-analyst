import httpx
import yfinance as yf
from datetime import datetime, timezone


def get_gold_price() -> dict:
    """Fetch current gold spot price from metals.live.

    Returns:
        {"price": float, "change_pct": float, "timestamp": str ISO8601}
    """
    try:
        response = httpx.get("https://api.metals.live/v1/spot/gold", timeout=10)
        response.raise_for_status()
        price = float(response.json()[0].get("gold", 0))
    except Exception:
        price = 0.0

    try:
        hist = yf.Ticker("GC=F").history(period="2d")
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            change_pct = round((price - prev) / prev * 100, 2)
        else:
            change_pct = 0.0
    except Exception:
        change_pct = 0.0

    return {
        "price": price,
        "change_pct": change_pct,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
