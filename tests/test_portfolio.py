import os
import tempfile
import pytest
from portfolio import PortfolioState, load_portfolio, save_portfolio_entry, make_trade_decision, get_initial_state

_CASH = PortfolioState("2026-06-18", 3340.5, 5.0, "HOLD", 0.0, 10000.0, 10000.0)
_HOLDING = PortfolioState("2026-06-18", 3340.5, 7.5, "BUY", 2.994, 0.0, 9999.93)


def test_buy_when_score_high():
    result = make_trade_decision(7.5, _CASH, 3340.5, "2026-06-19")
    assert result.action == "BUY"
    assert result.cash == pytest.approx(0.0, abs=0.01)
    assert result.shares == pytest.approx(10000.0 / 3340.5, abs=0.001)


def test_sell_when_score_low():
    result = make_trade_decision(3.5, _HOLDING, 3350.0, "2026-06-19")
    assert result.action == "SELL"
    assert result.shares == 0.0
    assert result.cash == pytest.approx(2.994 * 3350.0, abs=0.01)


def test_hold_middle_range():
    result = make_trade_decision(5.5, _CASH, 3340.5, "2026-06-19")
    assert result.action == "HOLD"


def test_no_rebuy_when_already_holding():
    result = make_trade_decision(8.0, _HOLDING, 3360.0, "2026-06-19")
    assert result.action == "HOLD"


def test_save_and_load_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        tmp = f.name
    try:
        save_portfolio_entry(_CASH, tmp)
        loaded = load_portfolio(tmp)
        assert len(loaded) == 1
        assert loaded[0].date == "2026-06-18"
        assert loaded[0].total_value == pytest.approx(10000.0)
    finally:
        os.unlink(tmp)


def test_load_missing_file_returns_empty():
    assert load_portfolio("/tmp/nonexistent_poly.jsonl") == []


def test_initial_state():
    s = get_initial_state("2026-06-18")
    assert s.cash == 10000.0 and s.shares == 0.0 and s.total_value == 10000.0
