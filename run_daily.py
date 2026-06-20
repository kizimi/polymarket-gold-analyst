#!/usr/bin/env python3
"""Daily pipeline: collect -> analyze -> trade -> report -> notify -> chart."""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from collectors.gold_price import get_gold_price
from collectors.polymarket import get_gold_related_events
from collectors.macro import get_macro_data
from analyst import GoldAnalyst
from portfolio import load_portfolio, get_initial_state, make_trade_decision, save_portfolio_entry
from reporter import generate_report
from notifier import send_feishu
from chart_generator import generate_svg_chart


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    fred_key = os.getenv("FRED_API_KEY", "")
    feishu_url = os.getenv("FEISHU_WEBHOOK_URL", "")

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[{today}] 采集数据...")
    gold_data = get_gold_price()
    events = get_gold_related_events()
    macro_data = get_macro_data(fred_key)
    print(f"  金价 ${gold_data['price']:,.2f}  事件 {len(events)} 条  DXY {macro_data['dxy']}")

    print("分析信号...")
    analyst = GoldAnalyst(api_key=api_key)
    result = analyst.analyze(gold_data, events, macro_data)
    result.raw_data["date"] = today
    print(f"  {result.direction} ({result.score}/10)")

    print("更新持仓...")
    history = load_portfolio()
    current = history[-1] if history else get_initial_state(today)
    new_state = make_trade_decision(result.score, current, gold_data["price"], today)
    save_portfolio_entry(new_state)
    print(f"  {new_state.action}  账户 ${new_state.total_value:,.2f}")

    print("生成报告...")
    report_path = generate_report(result, new_state)
    print(f"  -> {report_path}")

    print("更新图表...")
    generate_svg_chart(load_portfolio(), "chart.svg")

    if feishu_url:
        print("推飞书...")
        ok = send_feishu(feishu_url, result, new_state)
        print(f"  {'OK' if ok else 'FAILED'}")

    print("完成。")


if __name__ == "__main__":
    main()
