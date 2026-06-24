import httpx
import yfinance as yf
from datetime import datetime, timezone


def _price_from_yfinance() -> tuple[float, float]:
    """Return (price, change_pct) from yfinance GC=F. Raises on failure."""
    hist = yf.Ticker("GC=F").history(period="5d")
    if hist.empty:
        raise ValueError("empty history")
    price = float(hist["Close"].iloc[-1])
    if len(hist) >= 2:
        prev = float(hist["Close"].iloc[-2])
        change_pct = round((price - prev) / prev * 100, 2)
    else:
        change_pct = 0.0
    return price, change_pct


def get_gold_price() -> dict:
    """Fetch current gold spot price.

    Primary: yfinance GC=F (futures, reliable).
    Fallback: metals.live spot API.
    Returns: {"price": float, "change_pct": float, "timestamp": str ISO8601}
    """
    price, change_pct = 0.0, 0.0

    try:
        price, change_pct = _price_from_yfinance()
    except Exception:
        try:
            response = httpx.get("https://api.metals.live/v1/spot/gold", timeout=10)
            response.raise_for_status()
            price = float(response.json()[0].get("gold", 0))
            change_pct = 0.0
        except Exception:
            pass

    return {
        "price": price,
        "change_pct": change_pct,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
