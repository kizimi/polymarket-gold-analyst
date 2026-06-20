import os
import tempfile
from analyst import AnalysisResult
from portfolio import PortfolioState
from reporter import generate_report

_A = AnalysisResult(
    score=7.2, direction="偏多",
    signals=[
        {"name": "降息预期", "icon": "🟢", "strength": "强", "detail": "78%"},
        {"name": "美元", "icon": "🟡", "strength": "中性", "detail": "DXY 104"},
        {"name": "地缘", "icon": "🟢", "strength": "强", "detail": "风险"},
        {"name": "动量", "icon": "🟢", "strength": "强", "detail": "涨0.8%"},
        {"name": "通胀", "icon": "🟡", "strength": "中性", "detail": "持平"},
    ],
    summary="多头信号占优。", recommendation="关注 $3,380。",
    raw_data={"gold": {"price": 3340.5, "change_pct": 0.8}},
)
_P = PortfolioState("2026-06-18", 3340.5, 7.2, "BUY", 2.994, 0.0, 10000.57)


def test_creates_markdown_file():
    with tempfile.TemporaryDirectory() as d:
        path = generate_report(_A, _P, output_dir=d)
        assert os.path.exists(path) and path.endswith(".md")


def test_report_contains_key_data():
    with tempfile.TemporaryDirectory() as d:
        path = generate_report(_A, _P, output_dir=d)
        content = open(path, encoding="utf-8").read()
        assert "7.2" in content
        assert "偏多" in content
        assert "BUY" in content
        assert "10000" in content
