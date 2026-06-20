from unittest.mock import patch, MagicMock
from collectors.polymarket import get_gold_related_events

MOCK_DATA = [
    {"title": "Will the Fed cut rates in September 2026?",
     "markets": [{"outcomePrices": "[0.78, 0.22]", "volume": "1500000"}]},
    {"title": "Will Russia escalate conflict in 2026?",
     "markets": [{"outcomePrices": "[0.35, 0.65]", "volume": "800000"}]},
    {"title": "Will Taylor Swift release a new album?",
     "markets": [{"outcomePrices": "[0.60, 0.40]", "volume": "500000"}]},
]


def _mock_resp(data):
    m = MagicMock()
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


def test_returns_list():
    with patch("collectors.polymarket.httpx.get", return_value=_mock_resp(MOCK_DATA)):
        assert isinstance(get_gold_related_events(), list)


def test_filters_non_gold_events():
    with patch("collectors.polymarket.httpx.get", return_value=_mock_resp(MOCK_DATA)):
        titles = [e["title"] for e in get_gold_related_events()]
    assert not any("Taylor Swift" in t for t in titles)


def test_required_keys_present():
    with patch("collectors.polymarket.httpx.get", return_value=_mock_resp(MOCK_DATA)):
        for event in get_gold_related_events():
            assert all(k in event for k in ("title", "probability", "category", "volume"))
            assert 0.0 <= event["probability"] <= 1.0


def test_probability_parsed_correctly():
    with patch("collectors.polymarket.httpx.get", return_value=_mock_resp(MOCK_DATA)):
        result = get_gold_related_events()
    fed = next(e for e in result if "Fed" in e["title"])
    assert abs(fed["probability"] - 0.78) < 0.001
