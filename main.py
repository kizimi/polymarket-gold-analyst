#!/usr/bin/env python3
"""
polymarket gold analyst — CLI
Usage:
    python main.py          # show today's signal + chat
    python main.py --today  # signal only, exit immediately
"""
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from collectors.gold_price import get_gold_price
from collectors.polymarket import get_gold_related_events
from collectors.macro import get_macro_data
from analyst import GoldAnalyst
from portfolio import load_portfolio, get_initial_state

_D = {"偏多": "⬆️", "中性": "➡️", "偏空": "⬇️"}


def _print_signal(result, gold_data: dict) -> None:
    price = gold_data.get("price", 0)
    chg = gold_data.get("change_pct", 0)
    sign = "+" if chg >= 0 else ""
    today = result.raw_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    print(f"\n📊 黄金信号摘要 [{today}]")
    print(f"黄金现价：${price:,.2f} / oz  ({sign}{chg}% 今日)\n")
    print(f"综合信号：{_D.get(result.direction,'➡️')} {result.direction}  ({result.score}/10)")
    for s in result.signals:
        print(f"• {s['name']}：{s['icon']} {s['strength']} — {s['detail']}")
    print(f"\n💡 {result.recommendation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gold Signal Analyst")
    parser.add_argument("--today", action="store_true", help="Print signal and exit")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    fred_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    print("🔍 采集数据中...")
    gold_data = get_gold_price()
    events = get_gold_related_events()
    macro_data = get_macro_data(fred_key)

    print("🤖 分析中...")
    analyst = GoldAnalyst(api_key=api_key)
    result = analyst.analyze(gold_data, events, macro_data)
    result.raw_data["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    _print_signal(result, gold_data)

    today = result.raw_data["date"]
    history = load_portfolio()
    current = history[-1] if history else get_initial_state(today)
    print(f"\n💼 模拟基金：${current.total_value:,.2f}  "
          f"(持仓 {current.shares:.4f} oz, 现金 ${current.cash:,.2f})")

    if args.today:
        return

    print('\n💬 追问任意问题，或输入 "quit" 退出\n')
    while True:
        try:
            question = input("❓ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question or question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        print(analyst.followup(question, result) + "\n")


if __name__ == "__main__":
    main()
