from unittest.mock import patch, MagicMock
from analyst import AnalysisResult
from portfolio import PortfolioState
from notifier import send_feishu

_A = AnalysisResult(
    score=7.2, direction="偏多",
    signals=[
        {"name": "降息预期", "icon": "🟢", "strength": "强", "detail": "78%"},
        {"name": "美元", "icon": "🟡", "strength": "中性", "detail": "104"},
        {"name": "地缘", "icon": "🟢", "strength": "强", "detail": "风险"},
        {"name": "动量", "icon": "🟢", "strength": "强", "detail": "涨0.8%"},
        {"name": "通胀", "icon": "🟡", "strength": "中性", "detail": "持平"},
    ],
    summary="多头。", recommendation="关注3380。",
    raw_data={"gold": {"price": 3340.5, "change_pct": 0.8}},
)
_P = PortfolioState("2026-06-18", 3340.5, 7.2, "BUY", 2.994, 0.0, 10000.57)
_URL = "https://open.feishu.cn/hook/test"


def test_returns_true_on_success():
    m = MagicMock()
    m.json.return_value = {"code": 0}
    m.raise_for_status = MagicMock()
    with patch("notifier.httpx.post", return_value=m):
        assert send_feishu(_URL, _A, _P) is True


def test_returns_false_on_error():
    with patch("notifier.httpx.post", side_effect=Exception("timeout")):
        assert send_feishu(_URL, _A, _P) is False


def test_posts_text_msg_type():
    captured = {}
    m = MagicMock()
    m.json.return_value = {"code": 0}
    m.raise_for_status = MagicMock()
    def cap(**kw): captured.update(kw); return m
    with patch("notifier.httpx.post", side_effect=cap):
        send_feishu(_URL, _A, _P)
    assert captured.get("json", {}).get("msg_type") == "text"
