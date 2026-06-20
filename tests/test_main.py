"""Tests for main.py CLI entry point."""
import sys
import pytest
from unittest.mock import patch, MagicMock
from analyst import AnalysisResult
from portfolio import PortfolioState

_GOLD = {"price": 3340.5, "change_pct": 0.8, "timestamp": "2026-06-18T00:00:00Z"}
_EVENTS = [{"title": "Gold > $3000", "probability": 0.95}]
_MACRO = {"dxy": 104.0, "fed_rate": 5.25, "us10y": 4.3}

_RESULT = AnalysisResult(
    score=7.2,
    direction="偏多",
    signals=[
        {"name": "降息预期", "icon": "🟢", "strength": "强", "detail": "78%"},
        {"name": "美元", "icon": "🟡", "strength": "中性", "detail": "DXY 104"},
        {"name": "地缘", "icon": "🟢", "strength": "强", "detail": "风险"},
        {"name": "动量", "icon": "🟢", "strength": "强", "detail": "涨0.8%"},
        {"name": "通胀", "icon": "🟡", "strength": "中性", "detail": "持平"},
    ],
    summary="多头信号占优。",
    recommendation="关注 $3,380。",
    raw_data={"date": "2026-06-18"},
)

_PORTFOLIO = PortfolioState("2026-06-18", 3340.5, 7.2, "BUY", 2.994, 0.0, 10000.57)


def _mock_analyst():
    m = MagicMock()
    m.analyze.return_value = _RESULT
    m.followup.return_value = "黄金短期偏多。"
    return m


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.GoldAnalyst", return_value=_mock_analyst())
@patch("main.load_portfolio", return_value=[_PORTFOLIO])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "fred-key"})
def test_today_flag_exits_cleanly(mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys):
    """--today flag should print signal and return without entering chat loop."""
    with patch("sys.argv", ["main.py", "--today"]):
        from main import main
        main()
    out = capsys.readouterr().out
    assert "黄金信号摘要" in out
    assert "综合信号" in out
    assert "模拟基金" in out


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.GoldAnalyst", return_value=_mock_analyst())
@patch("main.load_portfolio", return_value=[])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "fred-key"})
def test_uses_initial_state_when_no_history(mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys):
    """When portfolio is empty, falls back to get_initial_state."""
    with patch("sys.argv", ["main.py", "--today"]):
        from main import main
        main()
    out = capsys.readouterr().out
    assert "模拟基金" in out
    assert "$10,000.00" in out


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.GoldAnalyst", return_value=_mock_analyst())
@patch("main.load_portfolio", return_value=[_PORTFOLIO])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_followup_loop_handles_quit(mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys):
    """Chat loop exits cleanly on 'quit'."""
    with patch("sys.argv", ["main.py"]), patch("builtins.input", return_value="quit"):
        from main import main
        main()
    out = capsys.readouterr().out
    assert "Bye!" in out


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.GoldAnalyst", return_value=_mock_analyst())
@patch("main.load_portfolio", return_value=[_PORTFOLIO])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_followup_loop_handles_eof(mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys):
    """Chat loop exits cleanly on EOFError (piped input)."""
    with patch("sys.argv", ["main.py"]), patch("builtins.input", side_effect=EOFError):
        from main import main
        main()
    out = capsys.readouterr().out
    assert "Bye!" in out


@patch.dict("os.environ", {}, clear=True)
def test_missing_api_key_exits_with_error(capsys):
    """Missing ANTHROPIC_API_KEY should print error and exit(1)."""
    with patch("sys.argv", ["main.py", "--today"]):
        from main import main
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "ANTHROPIC_API_KEY" in out


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.GoldAnalyst", return_value=_mock_analyst())
@patch("main.load_portfolio", return_value=[_PORTFOLIO])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_signal_display_shows_all_signals(mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys):
    """Each signal name, icon, strength, and detail should appear in output."""
    with patch("sys.argv", ["main.py", "--today"]):
        from main import main
        main()
    out = capsys.readouterr().out
    for sig in _RESULT.signals:
        assert sig["name"] in out
        assert sig["icon"] in out
        assert sig["strength"] in out
        assert sig["detail"] in out


@patch("main.get_gold_price", return_value=_GOLD)
@patch("main.get_gold_related_events", return_value=_EVENTS)
@patch("main.get_macro_data", return_value=_MACRO)
@patch("main.load_portfolio", return_value=[_PORTFOLIO])
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_followup_question_calls_analyst(mock_lp, mock_macro, mock_events, mock_gold, capsys):
    """A real question in the loop should call analyst.followup and print result."""
    mock_analyst = _mock_analyst()
    with patch("main.GoldAnalyst", return_value=mock_analyst), \
         patch("sys.argv", ["main.py"]), \
         patch("builtins.input", side_effect=["现在适合买入吗", "quit"]):
        from main import main
        main()
    out = capsys.readouterr().out
    assert "黄金短期偏多" in out
    mock_analyst.followup.assert_called_once()
