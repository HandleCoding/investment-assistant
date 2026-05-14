import pandas as pd

from app.domain.analysis import AnalysisSummary, ScoreBreakdown
from app.indicators.risk import annualized_volatility, max_drawdown
from app.indicators.technical import moving_average, rate_of_change


class ScoringService:
    def classify_score(self, score: float) -> str:
        if score >= 85:
            return "强关注"
        if score >= 70:
            return "可观察"
        if score >= 55:
            return "中性观望"
        if score >= 40:
            return "风险偏高"
        return "暂不建议"

    def score_a_share(self, symbol: str, prices: pd.DataFrame) -> AnalysisSummary:
        if len(prices) < 60:
            score = ScoreBreakdown(total=0)
            return AnalysisSummary(
                symbol=symbol,
                score=score,
                conclusion="数据不足",
                reasons=[],
                risks=["至少需要 60 个交易日数据才能生成第一版分析。"],
                metrics={"price_count": len(prices)},
            )

        frame = prices.copy().sort_values("trade_date")
        close = frame["close"].astype(float)
        returns = close.pct_change().dropna()
        latest_close = float(close.iloc[-1])
        ma20 = float(moving_average(close, 20).iloc[-1])
        ma60 = float(moving_average(close, 60).iloc[-1])
        ma120_value = moving_average(close, 120).iloc[-1]
        ma120 = float(ma120_value) if not pd.isna(ma120_value) else None
        return_20d = float(rate_of_change(close, 20).iloc[-1])
        return_60d = float(rate_of_change(close, 60).iloc[-1])
        drawdown = max_drawdown(close)
        volatility = annualized_volatility(returns)

        technical_score = self._score_technical(latest_close, ma20, ma60, ma120)
        momentum_score = self._score_momentum(return_20d, return_60d)
        risk_score = self._score_risk(drawdown, volatility)
        raw_total = round(technical_score + momentum_score + risk_score, 2)
        total = round(raw_total / 60 * 100, 2)
        score = ScoreBreakdown(
            total=total,
            raw_total=raw_total,
            raw_max_score=60,
            technical=technical_score,
            momentum=momentum_score,
            risk=risk_score,
        )

        reasons = self._build_reasons(latest_close, ma20, ma60, ma120, return_20d, return_60d)
        risks = self._build_risks(drawdown, volatility, latest_close, ma60)
        metrics = {
            "latest_close": round(latest_close, 3),
            "ma20": round(ma20, 3),
            "ma60": round(ma60, 3),
            "ma120": round(ma120, 3) if ma120 is not None else None,
            "return_20d": round(return_20d, 4),
            "return_60d": round(return_60d, 4),
            "max_drawdown": round(drawdown, 4),
            "annualized_volatility": round(volatility, 4),
            "price_count": len(frame),
        }

        return AnalysisSummary(
            symbol=symbol,
            score=score,
            conclusion=self.classify_score(total),
            reasons=reasons,
            risks=risks,
            metrics=metrics,
        )

    def _score_technical(
        self,
        latest_close: float,
        ma20: float,
        ma60: float,
        ma120: float | None,
    ) -> float:
        score = 0.0
        if latest_close > ma20:
            score += 7
        if latest_close > ma60:
            score += 7
        if ma20 > ma60:
            score += 4
        if ma120 is not None and latest_close > ma120:
            score += 2
        return score

    def _score_momentum(self, return_20d: float, return_60d: float) -> float:
        score = 0.0
        if return_20d > 0:
            score += 7
        if return_60d > 0:
            score += 7
        if 0.03 <= return_20d <= 0.18:
            score += 3
        if return_60d <= 0.35:
            score += 3
        return score

    def _score_risk(self, drawdown: float, volatility: float) -> float:
        score = 20.0
        if drawdown < -0.35:
            score -= 8
        elif drawdown < -0.25:
            score -= 5
        elif drawdown < -0.15:
            score -= 2

        if volatility > 0.55:
            score -= 7
        elif volatility > 0.4:
            score -= 4
        elif volatility > 0.3:
            score -= 2
        return max(score, 0.0)

    def _build_reasons(
        self,
        latest_close: float,
        ma20: float,
        ma60: float,
        ma120: float | None,
        return_20d: float,
        return_60d: float,
    ) -> list[str]:
        reasons: list[str] = []
        if latest_close > ma20:
            reasons.append("股价站上 20 日均线，短线趋势偏强。")
        if latest_close > ma60:
            reasons.append("股价站上 60 日均线，中期趋势没有明显走坏。")
        if ma20 > ma60:
            reasons.append("20 日均线高于 60 日均线，短中期均线结构偏积极。")
        if ma120 is not None and latest_close > ma120:
            reasons.append("股价站上 120 日均线，长期趋势有支撑。")
        if return_20d > 0:
            reasons.append("近 20 个交易日收益为正。")
        if return_60d > 0:
            reasons.append("近 60 个交易日收益为正。")
        return reasons

    def _build_risks(
        self,
        drawdown: float,
        volatility: float,
        latest_close: float,
        ma60: float,
    ) -> list[str]:
        risks: list[str] = []
        if latest_close < ma60:
            risks.append("股价低于 60 日均线，中期趋势偏弱。")
        if drawdown < -0.25:
            risks.append("回看区间内最大回撤较大，需要控制仓位。")
        if volatility > 0.4:
            risks.append("年化波动率偏高，价格波动风险较大。")
        if not risks:
            risks.append("第一版规则未触发明显趋势或波动风险，但仍需结合基本面和估值。")
        return risks
