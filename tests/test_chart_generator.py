import os
import tempfile
from portfolio import PortfolioState
from chart_generator import generate_svg_chart

_H = [
    PortfolioState("2026-06-18", 3340.5, 7.2, "BUY",  2.994, 0.0,    10000.00),
    PortfolioState("2026-06-19", 3360.0, 7.5, "HOLD", 2.994, 0.0,    10057.36),
    PortfolioState("2026-06-20", 3320.0, 3.8, "SELL", 0.0,   9940.08, 9940.08),
]


def test_creates_svg_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "chart.svg")
        generate_svg_chart(_H, path)
        assert os.path.exists(path)


def test_output_contains_svg_tag():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "chart.svg")
        generate_svg_chart(_H, path)
        assert "<svg" in open(path, encoding="utf-8").read().lower()


def test_empty_history_no_crash():
    with tempfile.TemporaryDirectory() as d:
        generate_svg_chart([], os.path.join(d, "chart.svg"))
