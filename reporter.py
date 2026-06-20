import os
from datetime import datetime, timezone
from pathlib import Path
from analyst import AnalysisResult
from portfolio import PortfolioState

_D = {"偏多": "⬆️", "中性": "➡️", "偏空": "⬇️"}
_INITIAL = 10000.0


def generate_report(
    analysis: AnalysisResult,
    portfolio: PortfolioState,
    output_dir: str = "reports",
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(output_dir, f"{today}.md")

    gold = analysis.raw_data.get("gold", {})
    price = gold.get("price", 0)
    chg = gold.get("change_pct", 0)
    sign = "+" if chg >= 0 else ""
    pnl = portfolio.total_value - _INITIAL
    ps = "+" if pnl >= 0 else ""

    rows = "\n".join(
        f"| {s['name']} | {s['icon']} {s['strength']} | {s['detail']} |"
        for s in analysis.signals
    )

    Path(path).write_text(f"""# 黄金日报 {today}

## 市场摘要

| 项目 | 数值 |
|---|---|
| 黄金现价 | ${price:,.2f} / oz |
| 今日涨跌 | {sign}{chg}% |
| 综合信号 | {_D.get(analysis.direction,'➡️')} {analysis.direction} ({analysis.score}/10) |

## 信号详情

| 信号 | 强度 | 说明 |
|---|---|---|
{rows}

## 分析结论

{analysis.summary}

**建议：** {analysis.recommendation}

## 模拟基金

| 项目 | 数值 |
|---|---|
| 今日操作 | {portfolio.action} |
| 黄金持仓 | {portfolio.shares:.4f} oz |
| 现金余额 | ${portfolio.cash:,.2f} |
| 账户总值 | ${portfolio.total_value:.2f} |
| 累计收益 | {ps}${pnl:,.2f} ({ps}{pnl/_INITIAL*100:.2f}%) |

---
*AI 自动生成，不构成投资建议。{datetime.now(timezone.utc).isoformat()}*
""", encoding="utf-8")
    return path
