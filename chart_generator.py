import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from portfolio import PortfolioState

_BG, _PANEL, _BLUE, _GOLD = "#0d1117", "#161b22", "#58a6ff", "#e3b341"
_GREEN, _RED, _MUTED, _FG, _GRID = "#3fb950", "#f85149", "#8b949e", "#e6edf3", "#21262d"


def generate_svg_chart(history: list[PortfolioState], output_path: str = "chart.svg") -> None:
    """Dark-theme SVG: portfolio value + gold price + buy/sell markers."""
    if not history:
        return

    dates = [datetime.strptime(e.date, "%Y-%m-%d") for e in history]
    values = [e.total_value for e in history]
    prices = [e.gold_price for e in history]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(_BG)
    ax1.set_facecolor(_BG)

    ax1.plot(dates, values, color=_BLUE, linewidth=2, label="Portfolio (USD)")
    ax1.set_ylabel("Portfolio ($)", color=_BLUE, fontsize=9)
    ax1.tick_params(axis="y", labelcolor=_BLUE)
    ax1.tick_params(axis="x", labelcolor=_MUTED)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=10))

    ax2 = ax1.twinx()
    ax2.plot(dates, prices, color=_GOLD, linewidth=1.5, linestyle="--", label="Gold ($/oz)")
    ax2.set_ylabel("Gold ($/oz)", color=_GOLD, fontsize=9)
    ax2.tick_params(axis="y", labelcolor=_GOLD)

    for date, val, entry in zip(dates, values, history):
        if entry.action == "BUY":
            ax1.annotate("▲", xy=(date, val), color=_GREEN, fontsize=11, ha="center", va="bottom")
        elif entry.action == "SELL":
            ax1.annotate("▼", xy=(date, val), color=_RED, fontsize=11, ha="center", va="top")

    pnl = values[-1] - 10000.0
    sign = "+" if pnl >= 0 else ""
    ax1.set_title(f"AI Gold Fund  |  ${values[-1]:,.2f}  ({sign}${pnl:,.2f})", color=_FG, fontsize=11, pad=10)

    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper left",
               facecolor=_PANEL, labelcolor=_FG, fontsize=8)

    for ax in (ax1, ax2):
        for spine in ax.spines.values():
            spine.set_color(_GRID)
    ax1.grid(color=_GRID, linestyle="--", linewidth=0.5)

    plt.tight_layout()
    plt.savefig(output_path, format="svg", bbox_inches="tight", facecolor=_BG)
    plt.close()
