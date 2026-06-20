import httpx
import yfinance as yf


def get_macro_data(fred_api_key: str) -> dict:
    """Fetch DXY, fed funds rate, and 10Y treasury yield.

    Returns:
        {"dxy": float, "dxy_change_pct": float, "fed_funds_rate": float, "treasury_10y": float}
    """
    hist = yf.Ticker("DX-Y.NYB").history(period="2d")
    if len(hist) >= 2:
        dxy = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        dxy_change = round((dxy - prev) / prev * 100, 2)
    elif len(hist) == 1:
        dxy = float(hist["Close"].iloc[-1])
        dxy_change = 0.0
    else:
        dxy = dxy_change = 0.0

    return {
        "dxy": round(dxy, 2),
        "dxy_change_pct": dxy_change,
        "fed_funds_rate": _fred(fred_api_key, "DFF"),
        "treasury_10y": _fred(fred_api_key, "DGS10"),
    }


def _fred(api_key: str, series_id: str) -> float:
    try:
        resp = httpx.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "api_key": api_key,
                    "file_type": "json", "sort_order": "desc", "limit": 1},
            timeout=10,
        )
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        if obs:
            return float(obs[0]["value"])
    except Exception:
        pass
    return 0.0
