import json
import httpx

_KEYWORDS = [
    "fed", "fomc", "interest rate", "rate cut", "rate hike",
    "dollar", "dxy",
    "war", "conflict", "middle east", "russia", "ukraine", "taiwan",
    "cpi", "pce", "inflation",
]

_CATEGORIES = [
    ({"fed", "fomc", "interest rate", "rate cut", "rate hike"}, "fed_rate"),
    ({"dollar", "dxy"}, "dollar"),
    ({"war", "conflict", "middle east", "russia", "ukraine", "taiwan"}, "geopolitical"),
    ({"cpi", "pce", "inflation"}, "inflation"),
]


def _categorize(title: str) -> str:
    lower = title.lower()
    for keywords, cat in _CATEGORIES:
        if any(kw in lower for kw in keywords):
            return cat
    return "other"


def get_gold_related_events() -> list[dict]:
    """Fetch Polymarket events related to gold price drivers."""
    params = {"limit": 100, "active": "true", "order": "volume", "ascending": "false"}
    resp = httpx.get("https://gamma-api.polymarket.com/events", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events", data) if isinstance(data, dict) else data

    result = []
    for ev in events:
        title = ev.get("title", "")
        if not any(kw in title.lower() for kw in _KEYWORDS):
            continue
        markets = ev.get("markets", [])
        if not markets:
            continue
        try:
            prices = json.loads(markets[0].get("outcomePrices", "[0.5,0.5]"))
            prob = float(prices[0])
        except (json.JSONDecodeError, IndexError, ValueError):
            prob = 0.5
        result.append({
            "title": title,
            "probability": round(prob, 4),
            "category": _categorize(title),
            "volume": float(markets[0].get("volume", 0)),
        })
    return result
