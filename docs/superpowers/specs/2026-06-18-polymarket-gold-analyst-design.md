# Polymarket Gold Analyst — 设计文档

**日期：** 2026-06-18  
**项目目录：** `/Users/alan/CC/polymarket/`  
**目标：** 结合 Polymarket 预测市场数据、黄金现价、宏观指标，通过 Claude 推理生成黄金投资信号，每日推送飞书机器人，支持 CLI 追问。

---

## 1. 架构概览

```
collectors/
  polymarket.py     ← Polymarket Gamma/CLOB API（免认证）
  gold_price.py     ← metals.live 黄金现价（免认证）
  macro.py          ← Yahoo Finance (DXY) + FRED (利率预期)
        │
        ▼
analyst.py          ← Claude claude-sonnet-4-6，tool_use 模式
  - 聚合三路数据，评分 0-10
  - 生成综合信号 + 简洁结论
  - 支持追问（drill-down）
        │
   ┌────┴────┐
   ▼         ▼
main.py    reporter.py
(CLI)      (日报 markdown → reports/YYYY-MM-DD.md)
                │
                ▼
           notifier.py
           (飞书 Webhook 推送摘要)
                │
                ▼
  .github/workflows/daily-report.yml
  (GitHub Actions，北京时间 08:00 自动触发)
```

---

## 2. 目录结构

```
polymarket/
├── .github/
│   └── workflows/
│       └── daily-report.yml       # GitHub Actions 定时任务
├── collectors/
│   ├── __init__.py
│   ├── polymarket.py              # Polymarket 数据采集
│   ├── gold_price.py              # 黄金现价采集
│   └── macro.py                   # 宏观数据采集（DXY、利率预期）
├── memory/
│   ├── signals.jsonl              # 历史信号记录（时间戳 + 信号 + 结论）
│   └── context.md                 # 黄金投资背景知识、关键事件定义
├── reports/                       # 日报输出目录（Git 追踪）
├── analyst.py                     # Claude 推理层
├── main.py                        # CLI 交互入口
├── reporter.py                    # 日报生成
├── notifier.py                    # 飞书 Webhook 推送
├── .env                           # 本地开发用（不提交 git）
├── .env.example                   # key 模板
├── requirements.txt
└── CLAUDE.md
```

---

## 3. 数据源

| 数据源 | 用途 | 接口 | 认证 |
|---|---|---|---|
| Polymarket Gamma API | 事件列表、赔率 | `https://gamma-api.polymarket.com` | 无需 |
| Polymarket CLOB API | 历史价格 | `https://clob.polymarket.com` | 无需 |
| metals.live | 黄金现价 | `https://api.metals.live/v1/spot/gold` | 无需 |
| Yahoo Finance (yfinance) | 美元指数 DXY | `yfinance` Python 库 | 无需 |
| FRED API | 美联储利率预期 | `https://api.stlouisfed.org/fred/series` | 免费注册 key |

---

## 4. 信号系统

### 4.1 Polymarket 筛选维度

从 Polymarket 自动筛选与黄金价格强相关的事件关键词：
- 美联储：`Fed rate cut`, `FOMC`, `interest rate`
- 美元：`dollar`, `DXY`
- 地缘政治：`war`, `conflict`, `Middle East`, `Russia`, `Ukraine`
- 通胀：`CPI`, `PCE`, `inflation`

### 4.2 信号评分（Claude 推理，0-10）

| 信号维度 | 多头方向 |
|---|---|
| 降息预期 | Polymarket 降息概率上升 |
| 美元强弱 | DXY 走弱 |
| 地缘风险 | 冲突升级概率上升 |
| 黄金动量 | 近期价格趋势向上 |
| 通胀预期 | 通胀预期上升 |

综合评分：Claude 加权推理，输出 0-10 分 + 方向（偏多/中性/偏空）。

### 4.3 输出格式

**CLI 默认输出（简洁信号）：**
```
📊 黄金信号摘要 [2026-06-18]
黄金现价：$3,340 / oz  (+0.8% 今日)

综合信号：⬆️ 偏多  (7.2/10)
• 降息预期：🟢 强 — Fed 9月降息概率 78%
• 美元：🟡 中性 — DXY 104.2，横盘
• 地缘：🟢 强 — 中东紧张局势升级概率 +12%
• 动量：🟢 强 — 金价连续3日新高
• 通胀：🟡 中性 — PCE 预期持平

💡 建议：当前多头信号占优，关注 $3,380 阻力位。
   输入"为什么"可追问任一信号的详细逻辑。
```

**飞书推送（摘要卡片）：**
```
📊 黄金日报 2026-06-18
现价：$3,340  今日 +0.8%
综合信号：⬆️ 偏多 (7.2/10)
• 降息预期 🟢  • 美元 🟡  • 地缘 🟢  • 动量 🟢  • 通胀 🟡
查看完整报告 → reports/2026-06-18.md
```

**日报文件（`reports/YYYY-MM-DD.md`）：** 包含原始数据、信号评分、完整推理过程，Git 追踪作为投资笔记。

---

## 5. GitHub Actions 定时任务

**触发时间：** 北京时间每天 08:00（UTC 00:00）

**工作流程：**
1. checkout 代码
2. 安装依赖
3. 运行 `reporter.py`（采集 + 分析 + 生成报告）
4. 运行 `notifier.py`（推送飞书）
5. commit & push `reports/YYYY-MM-DD.md` 到仓库

**GitHub Secrets（需手动配置）：**
- `ANTHROPIC_API_KEY`
- `FRED_API_KEY`
- `FEISHU_WEBHOOK_URL`

---

## 6. 环境变量

```env
ANTHROPIC_API_KEY=...
FRED_API_KEY=...           # 免费注册 https://fred.stlouisfed.org/docs/api/api_key.html
FEISHU_WEBHOOK_URL=...     # 飞书群机器人 Webhook URL
```

---

## 7. 技术栈

- **语言：** Python 3.11+
- **HTTP：** `httpx`（异步采集）
- **宏观数据：** `yfinance`
- **AI：** `anthropic` SDK，`claude-sonnet-4-6`，tool_use 模式
- **定时：** GitHub Actions cron
- **通知：** 飞书 Incoming Webhook（POST JSON）

---

## 8. MVP 范围（第一版）

**包含：**
- 三路数据采集（Polymarket + 黄金价格 + 宏观）
- Claude 信号聚合 + 评分
- CLI 交互（简洁输出 + 追问）
- 日报生成（markdown）
- 飞书推送
- GitHub Actions 定时

**不包含（后期迭代）：**
- Polymarket WebSocket 实时订阅
- 历史信号回测
- 多品种支持（仅黄金）
- Web 界面
