from unittest.mock import patch, MagicMock
from collectors.gold_price import get_gold_price


def test_returns_required_keys():
    with patch("collectors.gold_price._price_from_yfinance", return_value=(3340.5, 0.81)):
        result = get_gold_price()
    assert "price" in result and "change_pct" in result and "timestamp" in result


def test_price_from_yfinance_primary():
    with patch("collectors.gold_price._price_from_yfinance", return_value=(3340.5, 0.81)):
        result = get_gold_price()
    assert result["price"] == 3340.5
    assert result["change_pct"] == 0.81


def test_falls_back_to_metals_live_when_yfinance_fails():
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"gold": 3320.0}]
    with patch("collectors.gold_price._price_from_yfinance", side_effect=Exception("yf down")):
        with patch("collectors.gold_price.httpx.get", return_value=mock_resp):
            result = get_gold_price()
    assert result["price"] == 3320.0
