# Polymarket Gold Analyst Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered gold investment signal system that collects data from Polymarket, gold price APIs, and macro indicators, analyzes them with Claude, manages a simulated $10,000 fund, pushes daily reports to Feishu, and displays a live dashboard on GitHub Pages.

**Architecture:** Three independent data collectors feed a Claude-powered analyst that scores gold signals 0-10. A portfolio tracker executes simulated trades based on signal thresholds. A chart generator produces an SVG embedded in the README, and a GitHub Pages dashboard renders interactive charts. GitHub Actions runs the full pipeline daily at UTC 00:00 (Beijing 08:00) and commits results back to the repo.

**Tech Stack:** Python 3.11+, httpx, yfinance, anthropic SDK (claude-sonnet-4-6), matplotlib (SVG), Chart.js via CDN (dashboard), GitHub Actions

## Global Constraints

- Python 3.11+
- All collectors return plain dicts — no external types leak between modules
- No paid APIs: metals.live (free), FRED (free key), Yahoo Finance via yfinance (free), Polymarket (public)
- `portfolio.jsonl`: one JSON object per line, date field format `YYYY-MM-DD`
- All monetary values: USD float; gold price: USD per troy ounce
- Claude model: `claude-sonnet-4-6`
- Feishu webhook: POST `application/json` to `FEISHU_WEBHOOK_URL`
- GitHub Actions cron: `'0 0 * * *'` (UTC 00:00 = Beijing 08:00)
- Signal thresholds: BUY >= 7.0, SELL <= 4.0, HOLD otherwise
- Simulated fund starts: $10,000 cash, 0 gold shares

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `CLAUDE.md`
- Create: `collectors/__init__.py`
- Create: `memory/context.md`
- Create: `memory/signals.jsonl` (empty)
- Create: `reports/.gitkeep`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: project structure all later tasks build into

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.40.0
httpx>=0.27.0
yfinance>=0.2.40
python-dotenv>=1.0.0
matplotlib>=3.9.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 2: Create .env.example**

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
FRED_API_KEY=your_fred_api_key_here
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your_token_here
```

- [ ] **Step 3: Create .gitignore**

```
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
.DS_Store
```

- [ ] **Step 4: Create collectors/__init__.py** (empty file)

- [ ] **Step 5: Create tests/__init__.py** (empty file)

- [ ] **Step 6: Create memory/context.md**

```markdown
# 黄金投资背景知识

## 关键驱动因素

- **美联储利率：** 降息预期上升 -> 黄金多头（实际利率下降，黄金持有成本降低）
- **美元指数 DXY：** DXY 走弱 -> 黄金多头（黄金以美元计价，美元弱则黄金贵）
- **地缘政治：** 冲突升级 -> 避险需求 -> 黄金多头
- **通胀预期：** CPI/PCE 上升 -> 黄金保值需求 -> 黄金多头

## 信号评分规则

- 综合评分 >= 7.0：买入信号（全仓买入）
- 综合评分 <= 4.0：卖出信号（全仓卖出）
- 4.0 ~ 7.0：持仓不动

## Polymarket 关键词

- 美联储：Fed rate cut, FOMC, interest rate, rate hike
- 美元：dollar index, DXY
- 地缘：war, conflict, Middle East, Russia, Ukraine, Taiwan
- 通胀：CPI, PCE, inflation
```

- [ ] **Step 7: Create empty placeholder files**

```bash
touch reports/.gitkeep memory/signals.jsonl
```

- [ ] **Step 8: Create CLAUDE.md**

```markdown
# polymarket — Gold Signal Analyst

## 项目目标
用 Polymarket 预测市场数据 + 黄金现价 + 宏观指标，通过 Claude 生成黄金投资信号，
管理一个 $10,000 模拟基金，每日推飞书。

## 核心文件
- `run_daily.py` — 每日完整流水线（GitHub Actions 调用）
- `main.py` — 本地 CLI 交互入口
- `analyst.py` — Claude 信号推理层
- `portfolio.py` — 模拟基金交易逻辑
- `collectors/` — 三路数据采集模块

## 信号阈值
- >= 7.0 -> BUY（全仓买入）
- <= 4.0 -> SELL（全仓卖出）
- 其余 -> HOLD

## 本地运行
cp .env.example .env  # 填入 keys
pip install -r requirements.txt
python main.py         # CLI 模式，支持追问
python run_daily.py    # 完整日报流水线
```

- [ ] **Step 9: Install dependencies**

```bash
cd /Users/alan/CC/polymarket && pip install -r requirements.txt
```

Expected: all packages install without errors

- [ ] **Step 10: Commit scaffold**

```bash
git add .
git commit -m "feat: scaffold polymarket gold analyst project"
```

---

### Task 2: Gold Price Collector

**Files:**
- Create: `collectors/gold_price.py`
- Create: `tests/test_gold_price.py`

**Interfaces:**
- Produces: `get_gold_price() -> dict` with keys `price: float`, `change_pct: float`, `timestamp: str` (ISO 8601)

- [ ] **Step 1: Write failing test**

```python
# tests/test_gold_price.py
from unittest.mock import patch, MagicMock
import pandas as pd
from collectors.gold_price import get_gold_price


def _mock_metals(price: float):
    m = MagicMock()
    m.json.return_value = [{"gold": price}]
    m.raise_for_status = MagicMock()
    return m


def _mock_yf(today: float, yesterday: float):
    t = MagicMock()
    t.history.return_value = pd.DataFrame(
        {"Close": [yesterday, today]},
        index=pd.date_range("2026-06-17", periods=2),
    )
    return t


def test_returns_required_keys():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    assert "price" in result and "change_pct" in result and "timestamp" in result


def test_price_is_positive_float():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    assert isinstance(result["price"], float) and result["price"] > 0


def test_change_pct_calculation():
    with patch("httpx.get", return_value=_mock_metals(3340.5)):
        with patch("yfinance.Ticker", return_value=_mock_yf(3340.5, 3313.8)):
            result = get_gold_price()
    expected = round((3340.5 - 3313.8) / 3313.8 * 100, 2)
    assert abs(result["change_pct"] - expected) < 0.01
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_gold_price.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement collectors/gold_price.py**

```python
import httpx
import yfinance as yf
from datetime import datetime, timezone


def get_gold_price() -> dict:
    """Fetch current gold spot price from metals.live.

    Returns:
        {"price": float, "change_pct": float, "timestamp": str ISO8601}
    """
    response = httpx.get("https://api.metals.live/v1/spot/gold", timeout=10)
    response.raise_for_status()
    price = float(response.json()[0].get("gold", 0))

    try:
        hist = yf.Ticker("GC=F").history(period="2d")
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            change_pct = round((price - prev) / prev * 100, 2)
        else:
            change_pct = 0.0
    except Exception:
        change_pct = 0.0

    return {
        "price": price,
        "change_pct": change_pct,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_gold_price.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add collectors/gold_price.py tests/test_gold_price.py
git commit -m "feat: add gold price collector"
```

---

### Task 3: Polymarket Collector

**Files:**
- Create: `collectors/polymarket.py`
- Create: `tests/test_polymarket.py`

**Interfaces:**
- Produces: `get_gold_related_events() -> list[dict]` each dict has: `title: str`, `probability: float` (0-1), `category: str`, `volume: float`

- [ ] **Step 1: Write failing test**

```python
# tests/test_polymarket.py
from unittest.mock import patch, MagicMock
from collectors.polymarket import get_gold_related_events

MOCK_DATA = [
    {"title": "Will the Fed cut rates in September 2026?",
     "markets": [{"outcomePrices": "[0.78, 0.22]", "volume": "1500000"}]},
    {"title": "Will Russia escalate conflict in 2026?",
     "markets": [{"outcomePrices": "[0.35, 0.65]", "volume": "800000"}]},
    {"title": "Will Taylor Swift release a new album?",
     "markets": [{"outcomePrices": "[0.60, 0.40]", "volume": "500000"}]},
]


def _mock_resp(data):
    m = MagicMock()
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


def test_returns_list():
    with patch("httpx.get", return_value=_mock_resp(MOCK_DATA)):
        assert isinstance(get_gold_related_events(), list)


def test_filters_non_gold_events():
    with patch("httpx.get", return_value=_mock_resp(MOCK_DATA)):
        titles = [e["title"] for e in get_gold_related_events()]
    assert not any("Taylor Swift" in t for t in titles)


def test_required_keys_present():
    with patch("httpx.get", return_value=_mock_resp(MOCK_DATA)):
        for event in get_gold_related_events():
            assert all(k in event for k in ("title", "probability", "category", "volume"))
            assert 0.0 <= event["probability"] <= 1.0


def test_probability_parsed_correctly():
    with patch("httpx.get", return_value=_mock_resp(MOCK_DATA)):
        result = get_gold_related_events()
    fed = next(e for e in result if "Fed" in e["title"])
    assert abs(fed["probability"] - 0.78) < 0.001
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_polymarket.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement collectors/polymarket.py**

```python
import json
import httpx

_KEYWORDS = [
    "fed rate", "fomc", "interest rate", "rate cut", "rate hike",
    "dollar", "dxy",
    "war", "conflict", "middle east", "russia", "ukraine", "taiwan",
    "cpi", "pce", "inflation",
]

_CATEGORIES = [
    ({"fed rate", "fomc", "interest rate", "rate cut", "rate hike"}, "fed_rate"),
    ({"dollar", "dxy"}, "dollar"),
    ({"war", "conflict", "middle east", "russia", "ukraine", "taiwan"}, "geopolitical"),
    ({"cpi", "pce", "inflation"}, "inflation"),
]


def _categorize(title: str) -> str:
    lower = title.lower()
    for keywords, cat in _CATEGORIES:
        if any(kw in lower for kw in keywords):
            return cat
    return "other"


def get_gold_related_events() -> list[dict]:
    """Fetch Polymarket events related to gold price drivers."""
    params = {"limit": 100, "active": "true", "order": "volume", "ascending": "false"}
    resp = httpx.get("https://gamma-api.polymarket.com/events", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events", data) if isinstance(data, dict) else data

    result = []
    for ev in events:
        title = ev.get("title", "")
        if not any(kw in title.lower() for kw in _KEYWORDS):
            continue
        markets = ev.get("markets", [])
        if not markets:
            continue
        try:
            prices = json.loads(markets[0].get("outcomePrices", "[0.5,0.5]"))
            prob = float(prices[0])
        except (json.JSONDecodeError, IndexError, ValueError):
            prob = 0.5
        result.append({
            "title": title,
            "probability": round(prob, 4),
            "category": _categorize(title),
            "volume": float(markets[0].get("volume", 0)),
        })
    return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_polymarket.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add collectors/polymarket.py tests/test_polymarket.py
git commit -m "feat: add Polymarket collector for gold-related events"
```

---

### Task 4: Macro Data Collector

**Files:**
- Create: `collectors/macro.py`
- Create: `tests/test_macro.py`

**Interfaces:**
- Consumes: `fred_api_key: str`
- Produces: `get_macro_data(fred_api_key: str) -> dict` with keys: `dxy: float`, `dxy_change_pct: float`, `fed_funds_rate: float`, `treasury_10y: float`

- [ ] **Step 1: Write failing test**

```python
# tests/test_macro.py
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from collectors.macro import get_macro_data


def _mock_yf(today: float, yesterday: float):
    t = MagicMock()
    t.history.return_value = pd.DataFrame(
        {"Close": [yesterday, today]},
        index=pd.date_range("2026-06-17", periods=2),
    )
    return t


def _mock_fred(value: str):
    m = MagicMock()
    m.json.return_value = {"observations": [{"value": value}]}
    m.raise_for_status = MagicMock()
    return m


def test_returns_required_keys():
    with patch("yfinance.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    assert all(k in result for k in ("dxy", "dxy_change_pct", "fed_funds_rate", "treasury_10y"))


def test_dxy_change_pct():
    with patch("yfinance.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    expected = round((104.2 - 104.5) / 104.5 * 100, 2)
    assert result["dxy_change_pct"] == pytest.approx(expected, abs=0.01)


def test_fred_rate_parsed():
    with patch("yfinance.Ticker", return_value=_mock_yf(104.2, 104.5)):
        with patch("httpx.get", return_value=_mock_fred("5.33")):
            result = get_macro_data("test_key")
    assert result["fed_funds_rate"] == pytest.approx(5.33)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_macro.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement collectors/macro.py**

```python
import httpx
import yfinance as yf


def get_macro_data(fred_api_key: str) -> dict:
    """Fetch DXY, fed funds rate, and 10Y treasury yield.

    Returns:
        {"dxy": float, "dxy_change_pct": float, "fed_funds_rate": float, "treasury_10y": float}
    """
    hist = yf.Ticker("DX-Y.NYB").history(period="2d")
    if len(hist) >= 2:
        dxy = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        dxy_change = round((dxy - prev) / prev * 100, 2)
    elif len(hist) == 1:
        dxy = float(hist["Close"].iloc[-1])
        dxy_change = 0.0
    else:
        dxy = dxy_change = 0.0

    return {
        "dxy": round(dxy, 2),
        "dxy_change_pct": dxy_change,
        "fed_funds_rate": _fred(fred_api_key, "DFF"),
        "treasury_10y": _fred(fred_api_key, "DGS10"),
    }


def _fred(api_key: str, series_id: str) -> float:
    try:
        resp = httpx.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "api_key": api_key,
                    "file_type": "json", "sort_order": "desc", "limit": 1},
            timeout=10,
        )
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        if obs:
            return float(obs[0]["value"])
    except Exception:
        pass
    return 0.0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_macro.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add collectors/macro.py tests/test_macro.py
git commit -m "feat: add macro data collector (DXY + FRED)"
```

---

### Task 5: Portfolio Tracker

**Files:**
- Create: `portfolio.py`
- Create: `tests/test_portfolio.py`

**Interfaces:**
- Produces:
  - `PortfolioState` dataclass: `date: str`, `gold_price: float`, `signal_score: float`, `action: str`, `shares: float`, `cash: float`, `total_value: float`
  - `load_portfolio(path: str = "portfolio.jsonl") -> list[PortfolioState]`
  - `save_portfolio_entry(entry: PortfolioState, path: str = "portfolio.jsonl") -> None`
  - `make_trade_decision(signal_score: float, current: PortfolioState, gold_price: float, today: str) -> PortfolioState`
  - `get_initial_state(today: str) -> PortfolioState`

- [ ] **Step 1: Write failing test**

```python
# tests/test_portfolio.py
import os
import tempfile
import pytest
from portfolio import PortfolioState, load_portfolio, save_portfolio_entry, make_trade_decision, get_initial_state

_CASH = PortfolioState("2026-06-18", 3340.5, 5.0, "HOLD", 0.0, 10000.0, 10000.0)
_HOLDING = PortfolioState("2026-06-18", 3340.5, 7.5, "BUY", 2.994, 0.0, 9999.93)


def test_buy_when_score_high():
    result = make_trade_decision(7.5, _CASH, 3340.5, "2026-06-19")
    assert result.action == "BUY"
    assert result.cash == pytest.approx(0.0, abs=0.01)
    assert result.shares == pytest.approx(10000.0 / 3340.5, abs=0.001)


def test_sell_when_score_low():
    result = make_trade_decision(3.5, _HOLDING, 3350.0, "2026-06-19")
    assert result.action == "SELL"
    assert result.shares == 0.0
    assert result.cash == pytest.approx(2.994 * 3350.0, abs=0.01)


def test_hold_middle_range():
    result = make_trade_decision(5.5, _CASH, 3340.5, "2026-06-19")
    assert result.action == "HOLD"


def test_no_rebuy_when_already_holding():
    result = make_trade_decision(8.0, _HOLDING, 3360.0, "2026-06-19")
    assert result.action == "HOLD"


def test_save_and_load_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        tmp = f.name
    try:
        save_portfolio_entry(_CASH, tmp)
        loaded = load_portfolio(tmp)
        assert len(loaded) == 1
        assert loaded[0].date == "2026-06-18"
        assert loaded[0].total_value == pytest.approx(10000.0)
    finally:
        os.unlink(tmp)


def test_load_missing_file_returns_empty():
    assert load_portfolio("/tmp/nonexistent_poly.jsonl") == []


def test_initial_state():
    s = get_initial_state("2026-06-18")
    assert s.cash == 10000.0 and s.shares == 0.0 and s.total_value == 10000.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_portfolio.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement portfolio.py**

```python
import json
from dataclasses import dataclass, asdict
from pathlib import Path

PORTFOLIO_PATH = "portfolio.jsonl"
INITIAL_CASH = 10000.0
BUY_THRESHOLD = 7.0
SELL_THRESHOLD = 4.0


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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_portfolio.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add portfolio.py tests/test_portfolio.py
git commit -m "feat: add portfolio tracker with simulated trade logic"
```

---

### Task 6: Analyst (Claude Signal Engine)

**Files:**
- Create: `analyst.py`
- Create: `tests/test_analyst.py`

**Interfaces:**
- Consumes: gold dict (from Task 2), events list (Task 3), macro dict (Task 4)
- Produces:
  - `AnalysisResult` dataclass: `score: float`, `direction: str`, `signals: list[dict]`, `summary: str`, `recommendation: str`, `raw_data: dict`
  - `GoldAnalyst(api_key: str).analyze(gold_data, events, macro_data) -> AnalysisResult`
  - `GoldAnalyst.followup(question: str, context: AnalysisResult) -> str`

- [ ] **Step 1: Write failing test**

```python
# tests/test_analyst.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_analyst.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement analyst.py**

```python
import json
import anthropic
from dataclasses import dataclass, field

_SYSTEM = """你是一位专业的黄金投资分析师。收到三类数据：
1. 黄金现货价格及今日涨跌
2. Polymarket 预测市场事件及其概率
3. 宏观指标（DXY、美联储利率、10年期美债收益率）

只输出如下 JSON，不要有其他文字：
{
  "score": <float 0-10，10分为极强多头>,
  "direction": <"偏多"|"中性"|"偏空">,
  "signals": [
    {"name": "降息预期", "icon": <"🟢"|"🟡"|"🔴">, "strength": <"强"|"中性"|"弱">, "detail": "<说明>"},
    {"name": "美元",    "icon": "...", "strength": "...", "detail": "..."},
    {"name": "地缘",    "icon": "...", "strength": "...", "detail": "..."},
    {"name": "动量",    "icon": "...", "strength": "...", "detail": "..."},
    {"name": "通胀",    "icon": "...", "strength": "...", "detail": "..."}
  ],
  "summary": "<2-3句综合判断>",
  "recommendation": "<具体建议，含价格参考>"
}

评分（各维度最高2分）：降息预期强+2、美元走弱+2、地缘风险高+2、金价动量向上+2、通胀预期高+2"""


@dataclass
class AnalysisResult:
    score: float
    direction: str
    signals: list[dict]
    summary: str
    recommendation: str
    raw_data: dict = field(default_factory=dict)


class GoldAnalyst:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def analyze(self, gold_data: dict, events: list[dict], macro_data: dict) -> AnalysisResult:
        payload = json.dumps(
            {"gold": gold_data, "polymarket_events": events, "macro": macro_data},
            ensure_ascii=False, indent=2,
        )
        msg = self._client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": payload}],
        )
        text = msg.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        return AnalysisResult(
            score=float(parsed["score"]),
            direction=parsed["direction"],
            signals=parsed["signals"],
            summary=parsed["summary"],
            recommendation=parsed["recommendation"],
            raw_data={"gold": gold_data, "events": events, "macro": macro_data},
        )

    def followup(self, question: str, context: AnalysisResult) -> str:
        prior = json.dumps({
            "score": context.score, "direction": context.direction,
            "signals": context.signals, "summary": context.summary,
            "recommendation": context.recommendation,
        }, ensure_ascii=False)
        msg = self._client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            system=_SYSTEM + "\n\n用户在追问，用自然语言详细回答，不需要输出 JSON。",
            messages=[
                {"role": "user", "content": json.dumps(context.raw_data, ensure_ascii=False)},
                {"role": "assistant", "content": prior},
                {"role": "user", "content": question},
            ],
        )
        return msg.content[0].text.strip()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_analyst.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analyst.py tests/test_analyst.py
git commit -m "feat: add Claude-powered gold signal analyst"
```

---

### Task 7: Reporter (Daily Markdown)

**Files:**
- Create: `reporter.py`
- Create: `tests/test_reporter.py`

**Interfaces:**
- Consumes: `AnalysisResult` (Task 6), `PortfolioState` (Task 5)
- Produces: `generate_report(analysis: AnalysisResult, portfolio: PortfolioState, output_dir: str = "reports") -> str` (file path)

- [ ] **Step 1: Write failing test**

```python
# tests/test_reporter.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_reporter.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement reporter.py**

```python
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
| 账户总值 | ${portfolio.total_value:,.2f} |
| 累计收益 | {ps}${pnl:,.2f} ({ps}{pnl/_INITIAL*100:.2f}%) |

---
*AI 自动生成，不构成投资建议。{datetime.now(timezone.utc).isoformat()}*
""", encoding="utf-8")
    return path
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_reporter.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reporter.py tests/test_reporter.py
git commit -m "feat: add daily markdown report generator"
```

---

### Task 8: Notifier (Feishu Webhook)

**Files:**
- Create: `notifier.py`
- Create: `tests/test_notifier.py`

**Interfaces:**
- Consumes: `webhook_url: str`, `AnalysisResult` (Task 6), `PortfolioState` (Task 5)
- Produces: `send_feishu(webhook_url: str, analysis: AnalysisResult, portfolio: PortfolioState) -> bool`

- [ ] **Step 1: Write failing test**

```python
# tests/test_notifier.py
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
    with patch("httpx.post", return_value=m):
        assert send_feishu(_URL, _A, _P) is True


def test_returns_false_on_error():
    with patch("httpx.post", side_effect=Exception("timeout")):
        assert send_feishu(_URL, _A, _P) is False


def test_posts_text_msg_type():
    captured = {}
    m = MagicMock()
    m.json.return_value = {"code": 0}
    m.raise_for_status = MagicMock()
    def cap(**kw): captured.update(kw); return m
    with patch("httpx.post", side_effect=cap):
        send_feishu(_URL, _A, _P)
    assert captured.get("json", {}).get("msg_type") == "text"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_notifier.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement notifier.py**

```python
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
        resp = httpx.post(webhook_url, json={"msg_type": "text", "content": {"text": text}}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("code", -1) == 0
    except Exception:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_notifier.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add notifier.py tests/test_notifier.py
git commit -m "feat: add Feishu webhook notifier"
```

---

### Task 9: Chart Generator (README SVG)

**Files:**
- Create: `chart_generator.py`
- Create: `tests/test_chart_generator.py`

**Interfaces:**
- Consumes: `list[PortfolioState]` (from Task 5)
- Produces: `generate_svg_chart(history: list[PortfolioState], output_path: str = "chart.svg") -> None`

- [ ] **Step 1: Write failing test**

```python
# tests/test_chart_generator.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_chart_generator.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement chart_generator.py**

```python
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

    ax1.plot(dates, values, color=_BLUE, linewidth=2, label="账户价值 (USD)")
    ax1.set_ylabel("账户价值 ($)", color=_BLUE, fontsize=9)
    ax1.tick_params(axis="y", labelcolor=_BLUE)
    ax1.tick_params(axis="x", labelcolor=_MUTED)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

    ax2 = ax1.twinx()
    ax2.plot(dates, prices, color=_GOLD, linewidth=1.5, linestyle="--", label="黄金价格 ($/oz)")
    ax2.set_ylabel("黄金价格 ($/oz)", color=_GOLD, fontsize=9)
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/test_chart_generator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add chart_generator.py tests/test_chart_generator.py
git commit -m "feat: add SVG chart generator for README"
```

---

### Task 10: GitHub Pages Dashboard

**Files:**
- Create: `docs/dashboard/index.html`

**Interfaces:**
- Consumes: `portfolio.jsonl` via GitHub raw URL (client-side fetch in browser)
- Produces: interactive Chart.js page at `https://GITHUB_USERNAME.github.io/REPO_NAME/dashboard/`

- [ ] **Step 1: Create docs/dashboard/index.html**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Gold Fund Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 24px; }
    h1 { font-size: 1.4rem; color: #58a6ff; margin-bottom: 4px; }
    .sub { color: #8b949e; font-size: 0.8rem; margin-bottom: 20px; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
    .stat { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; }
    .stat-l { font-size: 0.7rem; color: #8b949e; margin-bottom: 4px; }
    .stat-v { font-size: 1.3rem; font-weight: 600; }
    .pos { color: #3fb950; } .neg { color: #f85149; } .neu { color: #e6edf3; }
    .tbtn-wrap { display: flex; gap: 8px; margin-bottom: 12px; }
    .tbtn { background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.75rem; }
    .tbtn.active { background: #1f6feb; border-color: #58a6ff; color: #fff; }
    .chart-wrap { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 20px; height: 380px; position: relative; }
    .tbl { background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #21262d; padding: 8px 14px; text-align: left; font-size: 0.7rem; color: #8b949e; }
    td { padding: 8px 14px; border-top: 1px solid #21262d; font-size: 0.8rem; }
    .badge { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }
    .BUY { background: #1a4731; color: #3fb950; }
    .SELL { background: #3d1a1a; color: #f85149; }
    .HOLD { background: #1c2028; color: #8b949e; }
    .loading { text-align: center; padding: 32px; color: #8b949e; }
  </style>
</head>
<body>
  <h1>📈 AI Gold Fund Dashboard</h1>
  <p class="sub">Polymarket 信号驱动 · 模拟基金 $10,000 起</p>
  <div id="stats" class="stats"><div class="loading">加载中...</div></div>
  <div class="tbtn-wrap">
    <button class="tbtn active" onclick="filt(7,this)">7日</button>
    <button class="tbtn" onclick="filt(30,this)">30日</button>
    <button class="tbtn" onclick="filt(9999,this)">全部</button>
  </div>
  <div class="chart-wrap"><canvas id="chart"></canvas></div>
  <div class="tbl">
    <table>
      <thead><tr><th>日期</th><th>操作</th><th>信号</th><th>金价</th><th>账户值</th><th>收益</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
<script>
// Replace GITHUB_USERNAME and REPO_NAME after creating the repo
const RAW = "https://raw.githubusercontent.com/GITHUB_USERNAME/REPO_NAME/main/portfolio.jsonl";
let all = [], ch = null;

async function init() {
  try {
    const r = await fetch(RAW + "?t=" + Date.now());
    const txt = await r.text();
    all = txt.trim().split("\n").filter(Boolean).map(JSON.parse);
    render(all);
  } catch(e) {
    document.getElementById("stats").innerHTML = `<div class="loading">加载失败: ${e.message}</div>`;
  }
}

function filt(days, btn) {
  document.querySelectorAll(".tbtn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  const cut = new Date(); cut.setDate(cut.getDate() - days);
  render(all.filter(d => new Date(d.date) >= cut) || all);
}

function fmt(n, d=2) { return n.toLocaleString("en", {minimumFractionDigits:d, maximumFractionDigits:d}); }

function render(data) {
  if (!data.length) return;
  const last = data[data.length-1];
  const pnl = last.total_value - 10000;
  const pct = (pnl/100).toFixed(2);
  const cls = pnl >= 0 ? "pos" : "neg";
  const s = pnl >= 0 ? "+" : "";
  document.getElementById("stats").innerHTML = `
    <div class="stat"><div class="stat-l">账户总值</div><div class="stat-v neu">$${fmt(last.total_value)}</div></div>
    <div class="stat"><div class="stat-l">累计收益</div><div class="stat-v ${cls}">${s}$${fmt(Math.abs(pnl))}</div></div>
    <div class="stat"><div class="stat-l">收益率</div><div class="stat-v ${cls}">${s}${pct}%</div></div>
    <div class="stat"><div class="stat-l">今日金价</div><div class="stat-v neu">$${fmt(last.gold_price,0)}</div></div>
    <div class="stat"><div class="stat-l">今日信号</div><div class="stat-v neu">${last.signal_score}/10</div></div>
    <div class="stat"><div class="stat-l">运行天数</div><div class="stat-v neu">${data.length} 天</div></div>`;

  const labels = data.map(d=>d.date);
  const vals = data.map(d=>d.total_value);
  const prices = data.map(d=>d.gold_price);
  const buys = data.map((d,i)=>d.action==="BUY"?vals[i]:null);
  const sells = data.map((d,i)=>d.action==="SELL"?vals[i]:null);

  if (ch) ch.destroy();
  ch = new Chart(document.getElementById("chart"), {
    type:"line",
    data:{labels, datasets:[
      {label:"账户价值",data:vals,borderColor:"#58a6ff",backgroundColor:"rgba(88,166,255,0.07)",borderWidth:2,fill:true,tension:0.3,yAxisID:"y"},
      {label:"黄金价格",data:prices,borderColor:"#e3b341",borderDash:[5,5],borderWidth:1.5,fill:false,tension:0.3,yAxisID:"y2"},
      {label:"买入▲",data:buys,pointStyle:"triangle",pointRadius:9,pointBackgroundColor:"#3fb950",borderWidth:0,showLine:false,yAxisID:"y"},
      {label:"卖出▼",data:sells,pointStyle:"triangle",pointRadius:9,pointRotation:180,pointBackgroundColor:"#f85149",borderWidth:0,showLine:false,yAxisID:"y"},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:"#8b949e",font:{size:10}}}},
      scales:{
        x:{ticks:{color:"#8b949e",maxTicksLimit:8},grid:{color:"#21262d"}},
        y:{position:"left",ticks:{color:"#58a6ff",callback:v=>"$"+v.toLocaleString()},grid:{color:"#21262d"}},
        y2:{position:"right",ticks:{color:"#e3b341",callback:v=>"$"+v.toLocaleString()},grid:{drawOnChartArea:false}},
      },
    },
  });

  document.getElementById("tbody").innerHTML = [...data].reverse().slice(0,30).map(d=>{
    const p=d.total_value-10000; const ps=p>=0?"+":"";
    return `<tr><td>${d.date}</td><td><span class="badge ${d.action}">${d.action}</span></td>
      <td>${d.signal_score}</td><td>$${fmt(d.gold_price,0)}</td>
      <td>$${fmt(d.total_value)}</td>
      <td class="${p>=0?'pos':'neg'}">${ps}$${fmt(Math.abs(p))}</td></tr>`;
  }).join("");
}

init();
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add docs/dashboard/index.html
git commit -m "feat: add GitHub Pages interactive dashboard"
```

---

### Task 11: CLI Main Entry Point

**Files:**
- Create: `main.py`

**Interfaces:**
- Consumes: `get_gold_price`, `get_gold_related_events`, `get_macro_data`, `GoldAnalyst`, `load_portfolio`, `get_initial_state`
- Produces: CLI prints signal summary then enters followup loop

- [ ] **Step 1: Create main.py**

```python
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
```

- [ ] **Step 2: Smoke-test locally (requires .env with real keys)**

```bash
cd /Users/alan/CC/polymarket && python main.py --today
```
Expected: prints collection steps, signal summary, exits

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add CLI entry point with signal display and followup chat"
```

---

### Task 12: Daily Pipeline + GitHub Actions

**Files:**
- Create: `run_daily.py`
- Create: `.github/workflows/daily-report.yml`

**Interfaces:**
- Consumes: all modules above
- Produces: updated `portfolio.jsonl`, `reports/YYYY-MM-DD.md`, `chart.svg`, Feishu notification, git commit

- [ ] **Step 1: Create run_daily.py**

```python
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
```

- [ ] **Step 2: Create .github/workflows/daily-report.yml**

```yaml
name: Daily Gold Report

on:
  schedule:
    - cron: '0 0 * * *'   # UTC 00:00 = Beijing 08:00
  workflow_dispatch:        # manual trigger from GitHub UI

permissions:
  contents: write

jobs:
  daily-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run daily pipeline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
        run: python run_daily.py

      - name: Commit and push results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add portfolio.jsonl reports/ chart.svg
          git diff --staged --quiet || git commit -m "chore: daily report $(date -u +%Y-%m-%d)"
          git push
```

- [ ] **Step 3: Test pipeline locally**

```bash
cd /Users/alan/CC/polymarket && python run_daily.py
```
Expected: all steps print OK, `portfolio.jsonl` gets a new line, `reports/YYYY-MM-DD.md` created, `chart.svg` written

- [ ] **Step 4: Commit**

```bash
git add run_daily.py .github/workflows/daily-report.yml
git commit -m "feat: add daily pipeline and GitHub Actions workflow"
```

---

### Task 13: README + GitHub Repo Setup

**Files:**
- Create: `README.md`

**Interfaces:**
- Embeds `chart.svg`, links to GitHub Pages dashboard

- [ ] **Step 1: Create README.md**

```markdown
# 📈 AI Gold Fund — Polymarket Signal Analyst

> 由 Polymarket 预测市场信号驱动的黄金投资分析系统。
> 每天 08:00 (北京时间) 自动分析、模拟交易、推送飞书。

![Daily Report](https://github.com/GITHUB_USERNAME/REPO_NAME/actions/workflows/daily-report.yml/badge.svg)

## 最新信号

![AI Gold Fund Chart](chart.svg)

**[📊 查看完整交互看板 →](https://GITHUB_USERNAME.github.io/REPO_NAME/dashboard/)**

---

## 数据来源

| 数据 | 来源 | 说明 |
|---|---|---|
| 预测市场 | Polymarket | 降息/地缘/通胀事件概率（免认证 API） |
| 黄金价格 | metals.live | 现货价格 + 涨跌幅 |
| 宏观指标 | Yahoo Finance + FRED | DXY、美联储利率、10Y 美债 |

## 信号系统

| 综合评分 | 操作 |
|---|---|
| >= 7.0 | 买入（全仓） |
| 4.0 ~ 7.0 | 持仓不动 |
| <= 4.0 | 卖出（全仓） |

## 模拟基金

- 起始资金：$10,000 USD
- 开始日期：2026-06-18
- 策略：纯 AI 信号驱动，不加杠杆

## 本地运行

```bash
git clone https://github.com/GITHUB_USERNAME/REPO_NAME
cd REPO_NAME
cp .env.example .env   # 填入 keys
pip install -r requirements.txt
python main.py         # 查看今日信号，支持追问
python run_daily.py    # 完整日报流水线
```

## GitHub Secrets 配置

Settings -> Secrets -> Actions 中添加：

| Secret | 获取方式 |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `FRED_API_KEY` | fred.stlouisfed.org（免费注册） |
| `FEISHU_WEBHOOK_URL` | 飞书群 -> 机器人 -> 添加 Incoming Webhook |

---

*不构成投资建议。*
```

- [ ] **Step 2: Create GitHub repo and push**

```bash
cd /Users/alan/CC/polymarket
gh repo create polymarket-gold-analyst --public --description "AI gold signal system powered by Polymarket" --source=. --push
```

- [ ] **Step 3: Replace placeholders**

After repo is created, run `gh repo view --json url` to get the actual username/repo, then replace in:
- `README.md`: `GITHUB_USERNAME` and `REPO_NAME`
- `docs/dashboard/index.html`: `GITHUB_USERNAME` and `REPO_NAME` in the `RAW` const

```bash
git add README.md docs/dashboard/index.html
git commit -m "docs: set actual GitHub username and repo in links"
git push
```

- [ ] **Step 4: Enable GitHub Pages**

```bash
gh api repos/GITHUB_USERNAME/polymarket-gold-analyst/pages \
  --method POST \
  -f source.branch=main \
  -f source.path=/docs
```

Or via GitHub UI: Settings -> Pages -> Branch: main, folder: /docs -> Save

- [ ] **Step 5: Add GitHub Secrets**

```bash
gh secret set ANTHROPIC_API_KEY --body "$(grep ANTHROPIC_API_KEY /Users/alan/CC/polymarket/.env | cut -d= -f2)"
gh secret set FRED_API_KEY
gh secret set FEISHU_WEBHOOK_URL
```

- [ ] **Step 6: Trigger first workflow run**

```bash
gh workflow run daily-report.yml
gh run watch
```

Expected: Actions completes, `portfolio.jsonl` has first entry committed, Feishu message received, `chart.svg` in repo

- [ ] **Step 7: Run full test suite**

```bash
cd /Users/alan/CC/polymarket && python -m pytest tests/ -v
```
Expected: all tests PASS
