from app.domain.analysis import AnalysisSummary


class ReportService:
    def render_stock_markdown(self, summary: AnalysisSummary, market_name: str) -> str:
        metrics = summary.metrics
        score = summary.score
        reasons = "\n".join(f"- {reason}" for reason in summary.reasons) or "- 暂无明显积极信号。"
        risks = "\n".join(f"- {risk}" for risk in summary.risks) or "- 暂无明显风险信号。"

        return f"""# {summary.symbol} {market_name}股票分析报告

## 综合结论

- 结论：{summary.conclusion}
- 归一化评分：{score.total:.1f} / {score.max_score:.0f}
- 当前 MVP 原始分：{score.raw_total:.1f} / {score.raw_max_score:.0f}
- 说明：当前只包含趋势、动量、风险三类技术指标，尚未纳入基本面和估值。

## 核心指标

- 最新收盘价：{metrics.get("latest_close")}
- 20 日均线：{metrics.get("ma20")}
- 60 日均线：{metrics.get("ma60")}
- 120 日均线：{metrics.get("ma120")}
- 近 20 日收益：{self._format_percent(metrics.get("return_20d"))}
- 近 60 日收益：{self._format_percent(metrics.get("return_60d"))}
- 区间最大回撤：{self._format_percent(metrics.get("max_drawdown"))}
- 年化波动率：{self._format_percent(metrics.get("annualized_volatility"))}
- 使用价格数据条数：{metrics.get("price_count")}

## 积极因素

{reasons}

## 风险提示

{risks}

## 怎么理解

- 这不是买卖指令，只是第一版量化辅助判断。
- 如果结论是“可观察”，意思是可以加入观察池，不代表应该立刻买入。
- 如果短期收益为负但均线结构尚可，通常表示走势偏震荡，需要等待更明确的买点。
- 后续加入估值、财务、行业和基金数据后，结论会更完整。
"""

    def _format_percent(self, value: object) -> str:
        if not isinstance(value, int | float):
            return "N/A"
        return f"{value * 100:.2f}%"
