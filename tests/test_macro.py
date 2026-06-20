import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from collectors.macro import get_macro_data


def _mock_yf(today: float, yesterday: float):
    t = MagicMock()
    t.history.return_value = pd.DataFrame(
        {"Close": [yesterday, today]},
        index=pd.date_range("2026-06-17", periods=2),
    )
    return t


def _mock_fred(value: str):
    m = MagicMock()
    m.json.return_value = {"observations": [{"value": value}]}
    m.raise_for_status = MagicMock()
    return m


def test_returns_required_keys():
    with patch("collectors.macro.yf.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("collectors.macro.httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    assert all(k in result for k in ("dxy", "dxy_change_pct", "fed_funds_rate", "treasury_10y"))


def test_dxy_change_pct():
    with patch("collectors.macro.yf.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("collectors.macro.httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    expected = round((104.2 - 104.5) / 104.5 * 100, 2)
    assert result["dxy_change_pct"] == pytest.approx(expected, abs=0.01)


def test_fred_rate_parsed():
    with patch("collectors.macro.yf.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("collectors.macro.httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    assert result["fed_funds_rate"] == pytest.approx(5.33)
