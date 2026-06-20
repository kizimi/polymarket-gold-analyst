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
