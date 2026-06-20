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
