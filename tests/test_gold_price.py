from unittest.mock import patch, MagicMock
import pandas as pd
from collectors.gold_price import get_gold_price


def _mock_metals(price: float):
    m = MagicMock()
    m.json.return_value = [{"gold": price}]
    m.raise_for_status = MagicMock()
    return m


def _mock_yf(today: float, yesterday: float):
    t = MagicMock()
    t.history.return_value = pd.DataFrame(
        {"Close": [yesterday, today]},
        index=pd.date_range("2026-06-17", periods=2),
    )
    return t


def test_returns_required_keys():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    assert "price" in result and "change_pct" in result and "timestamp" in result


def test_price_is_positive_float():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    assert isinstance(result["price"], float) and result["price"] > 0


def test_change_pct_calculation():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    expected = round((3340.5 - 3313.8) / 3313.8 * 100, 2)
    assert abs(result["change_pct"] - expected) < 0.01
