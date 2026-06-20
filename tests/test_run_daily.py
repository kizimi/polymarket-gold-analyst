"""Tests for run_daily.py daily pipeline."""
import sys
import pytest
from unittest.mock import patch, MagicMock, call
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
    return m


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[_PORTFOLIO])
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "fred-key"})
def test_main_runs_full_pipeline(
    mock_chart, mock_report, mock_save, mock_trade, mock_lp,
    mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """main() should run all pipeline steps and print completion."""
    from run_daily import main
    main()
    out = capsys.readouterr().out
    assert "完成" in out
    mock_gold.assert_called_once()
    mock_events.assert_called_once()
    mock_macro.assert_called_once()
    mock_report.assert_called_once()
    mock_chart.assert_called_once()
    mock_save.assert_called_once_with(_PORTFOLIO)


@patch.dict("os.environ", {}, clear=True)
def test_missing_api_key_exits_with_error(capsys):
    """Missing ANTHROPIC_API_KEY should print error and exit(1)."""
    from run_daily import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "ANTHROPIC_API_KEY" in out


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[])
@patch("run_daily.get_initial_state", return_value=_PORTFOLIO)
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "fred-key"})
def test_uses_initial_state_when_no_history(
    mock_chart, mock_report, mock_save, mock_trade, mock_init,
    mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """When portfolio is empty, falls back to get_initial_state."""
    from run_daily import main
    main()
    mock_init.assert_called_once()
    out = capsys.readouterr().out
    assert "完成" in out


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[_PORTFOLIO])
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch("run_daily.send_feishu", return_value=True)
@patch.dict("os.environ", {
    "ANTHROPIC_API_KEY": "test-key",
    "FRED_API_KEY": "fred-key",
    "FEISHU_WEBHOOK_URL": "https://open.feishu.cn/open-apis/bot/v2/hook/test",
})
def test_feishu_called_when_url_set(
    mock_feishu, mock_chart, mock_report, mock_save, mock_trade,
    mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """send_feishu should be called when FEISHU_WEBHOOK_URL is set."""
    from run_daily import main
    main()
    mock_feishu.assert_called_once()
    out = capsys.readouterr().out
    assert "OK" in out


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[_PORTFOLIO])
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch("run_daily.send_feishu")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "fred-key"})
def test_feishu_skipped_when_no_url(
    mock_feishu, mock_chart, mock_report, mock_save, mock_trade,
    mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """send_feishu should NOT be called when FEISHU_WEBHOOK_URL is absent."""
    from run_daily import main
    main()
    mock_feishu.assert_not_called()


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[_PORTFOLIO])
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "FRED_API_KEY": "my-fred-key"})
def test_fred_key_passed_to_macro(
    mock_chart, mock_report, mock_save, mock_trade,
    mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """get_macro_data should receive FRED_API_KEY from environment."""
    from run_daily import main
    main()
    mock_macro.assert_called_once_with("my-fred-key")


@patch("run_daily.get_gold_price", return_value=_GOLD)
@patch("run_daily.get_gold_related_events", return_value=_EVENTS)
@patch("run_daily.get_macro_data", return_value=_MACRO)
@patch("run_daily.GoldAnalyst", return_value=_mock_analyst())
@patch("run_daily.load_portfolio", return_value=[_PORTFOLIO])
@patch("run_daily.make_trade_decision", return_value=_PORTFOLIO)
@patch("run_daily.save_portfolio_entry")
@patch("run_daily.generate_report", return_value="reports/2026-06-18.md")
@patch("run_daily.generate_svg_chart")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_output_shows_gold_price_and_events(
    mock_chart, mock_report, mock_save, mock_trade,
    mock_lp, mock_ga, mock_macro, mock_events, mock_gold, capsys
):
    """Output should include gold price and event count."""
    from run_daily import main
    main()
    out = capsys.readouterr().out
    assert "3,340.50" in out
    assert "1" in out  # 1 event
