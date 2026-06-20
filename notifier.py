import httpx
from analyst import AnalysisResult
from portfolio import PortfolioState

_D = {"偏多": "⬆️", "中性": "➡️", "偏空": "⬇️"}
_INITIAL = 10000.0


def send_feishu(webhook_url: str, analysis: AnalysisResult, portfolio: PortfolioState) -> bool:
    """POST daily summary to Feishu Incoming Webhook. Returns True on success."""
    gold = analysis.raw_data.get("gold", {})
    price = gold.get("price", 0)
    chg = gold.get("change_pct", 0)
    sign = "+" if chg >= 0 else ""
    pnl = portfolio.total_value - _INITIAL
    ps = "+" if pnl >= 0 else ""
    icons = "  ".join(f"{s['name']} {s['icon']}" for s in analysis.signals)
    text = (
        f"📊 黄金日报 {portfolio.date}\n"
        f"现价：${price:,.2f}  今日 {sign}{chg}%\n"
        f"综合信号：{_D.get(analysis.direction,'➡️')} {analysis.direction} ({analysis.score}/10)\n"
        f"{icons}\n"
        f"账户：${portfolio.total_value:,.2f}  ({ps}${pnl:,.2f})\n"
        f"今日操作：{portfolio.action}\n"
        f"💡 {analysis.recommendation}"
    )
    try:
        resp = httpx.post(url=webhook_url, json={"msg_type": "text", "content": {"text": text}}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("code", -1) == 0
    except Exception:
        return False
