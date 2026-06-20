import json
import pytest
from unittest.mock import MagicMock, patch
from analyst import GoldAnalyst, AnalysisResult

_GOLD = {"price": 3340.5, "change_pct": 0.8, "timestamp": "2026-06-18T00:00:00+00:00"}
_EVENTS = [{"title": "Fed rate cut Sep 2026?", "probability": 0.78, "category": "fed_rate", "volume": 1500000}]
_MACRO = {"dxy": 104.2, "dxy_change_pct": -0.3, "fed_funds_rate": 5.33, "treasury_10y": 4.25}

_CLAUDE_RESP = {
    "score": 7.2, "direction": "偏多",
    "signals": [
        {"name": "降息预期", "icon": "🟢", "strength": "强", "detail": "Fed 9月降息概率 78%"},
        {"name": "美元", "icon": "🟡", "strength": "中性", "detail": "DXY 104.2"},
        {"name": "地缘", "icon": "🟢", "strength": "强", "detail": "风险存在"},
        {"name": "动量", "icon": "🟢", "strength": "强", "detail": "涨0.8%"},
        {"name": "通胀", "icon": "🟡", "strength": "中性", "detail": "暂无新数据"},
    ],
    "summary": "多头信号占优。",
    "recommendation": "关注 $3,380 阻力位。",
}


def _mock_client(resp_json: dict):
    client = MagicMock()
    msg = MagicMock()
    content = MagicMock()
    content.type = "text"
    content.text = json.dumps(resp_json)
    msg.content = [content]
    client.messages.create.return_value = msg
    return client


def test_returns_analysis_result():
    with patch("anthropic.Anthropic", return_value=_mock_client(_CLAUDE_RESP)):
        result = GoldAnalyst("test").analyze(_GOLD, _EVENTS, _MACRO)
    assert isinstance(result, AnalysisResult)


def test_score_in_range():
    with patch("anthropic.Anthropic", return_value=_mock_client(_CLAUDE_RESP)):
        result = GoldAnalyst("test").analyze(_GOLD, _EVENTS, _MACRO)
    assert 0 <= result.score <= 10


def test_direction_valid():
    with patch("anthropic.Anthropic", return_value=_mock_client(_CLAUDE_RESP)):
        result = GoldAnalyst("test").analyze(_GOLD, _EVENTS, _MACRO)
    assert result.direction in ("偏多", "中性", "偏空")


def test_five_signals():
    with patch("anthropic.Anthropic", return_value=_mock_client(_CLAUDE_RESP)):
        result = GoldAnalyst("test").analyze(_GOLD, _EVENTS, _MACRO)
    assert len(result.signals) == 5


def test_raw_data_stored():
    with patch("anthropic.Anthropic", return_value=_mock_client(_CLAUDE_RESP)):
        result = GoldAnalyst("test").analyze(_GOLD, _EVENTS, _MACRO)
    assert "gold" in result.raw_data and "macro" in result.raw_data
