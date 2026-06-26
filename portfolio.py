import json
from dataclasses import dataclass, asdict
from pathlib import Path

PORTFOLIO_PATH = "portfolio.jsonl"
INITIAL_CASH = 10000.0
BUY_THRESHOLD = 6.0
SELL_THRESHOLD = 3.5


@dataclass
class PortfolioState:
    date: str
    gold_price: float
    signal_score: float
    action: str      # "BUY" | "SELL" | "HOLD"
    shares: float
    cash: float
    total_value: float


def load_portfolio(path: str = PORTFOLIO_PATH) -> list[PortfolioState]:
    p = Path(path)
    if not p.exists():
        return []
    return [
        PortfolioState(**json.loads(line))
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_portfolio_entry(entry: PortfolioState, path: str = PORTFOLIO_PATH) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry)) + "\n")


def make_trade_decision(
    signal_score: float,
    current: PortfolioState,
    gold_price: float,
    today: str,
) -> PortfolioState:
    if signal_score >= BUY_THRESHOLD and current.cash > 0:
        shares = current.shares + current.cash / gold_price
        return PortfolioState(today, gold_price, signal_score, "BUY",
                              round(shares, 6), 0.0, round(shares * gold_price, 2))
    if signal_score <= SELL_THRESHOLD and current.shares > 0:
        proceeds = current.cash + current.shares * gold_price
        return PortfolioState(today, gold_price, signal_score, "SELL",
                              0.0, round(proceeds, 2), round(proceeds, 2))
    total = current.cash + current.shares * gold_price
    return PortfolioState(today, gold_price, signal_score, "HOLD",
                          current.shares, current.cash, round(total, 2))


def get_initial_state(today: str) -> PortfolioState:
    return PortfolioState(today, 0.0, 5.0, "HOLD", 0.0, INITIAL_CASH, INITIAL_CASH)
