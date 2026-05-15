from abc import ABC, abstractmethod

import pandas as pd

from app.domain.strategy import StrategySignal
from app.indicators.risk import annualized_volatility, max_drawdown
from app.indicators.technical import moving_average, rate_of_change


class StrategyModule(ABC):
    name: str

    @abstractmethod
    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        raise NotImplementedError


class TrendMomentumStrategy(StrategyModule):
    name = "trend_momentum_quality"

    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        frame = _prepare(prices)
        latest = frame.iloc[-1]
        ret_20 = _last(rate_of_change(frame["close"], 20))
        ret_60 = _last(rate_of_change(frame["close"], 60))
        ret_120 = _last(rate_of_change(frame["close"], 120))
        ma20 = _last(moving_average(frame["close"], 20))
        ma60 = _last(moving_average(frame["close"], 60))
        ma120 = _last(moving_average(frame["close"], 120))
        volatility = annualized_volatility(frame["close"].pct_change().dropna())
        drawdown = max_drawdown(frame["close"])

        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []
        close = float(latest["close"])
        if ret_60 > 0.08:
            score += 25
            reasons.append("近 60 日趋势收益较强")
        if ret_120 > 0.12:
            score += 20
            reasons.append("近 120 日中期动量占优")
        if close > ma60 > ma120:
            score += 25
            reasons.append("价格位于 60/120 日均线上方")
        if ma20 > ma60:
            score += 15
            reasons.append("短期均线结构保持强势")
        if drawdown > -0.18:
            score += 10
            reasons.append("历史回撤相对可控")
        if volatility < 0.35:
            score += 5

        if ret_20 > 0.25:
            score -= 15
            risks.append("近 20 日涨幅过快，追高风险上升")
        if drawdown < -0.28:
            score -= 20
            risks.append("阶段最大回撤较深")
        if volatility > 0.45:
            score -= 10
            risks.append("年化波动率偏高")

        return _signal(
            self.name,
            symbol,
            market,
            score,
            close,
            holding_days=20,
            reasons=reasons,
            risks=risks,
            metrics={
                "return_20d": ret_20,
                "return_60d": ret_60,
                "return_120d": ret_120,
                "ma20": ma20,
                "ma60": ma60,
                "ma120": ma120,
                "volatility": volatility,
                "max_drawdown": drawdown,
            },
        )


class BreakoutVolumeStrategy(StrategyModule):
    name = "breakout_volume_confirmation"

    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        frame = _prepare(prices)
        close = float(frame.iloc[-1]["close"])
        previous_high = float(frame["high"].iloc[-61:-1].max())
        average_volume = float(frame["volume"].tail(20).mean() or 0)
        latest_volume = float(frame.iloc[-1].get("volume") or 0)
        volume_ratio = latest_volume / average_volume if average_volume else 1.0
        ret_20 = _last(rate_of_change(frame["close"], 20))
        drawdown = max_drawdown(frame["close"].tail(120))

        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []
        if close > previous_high:
            score += 45
            reasons.append("收盘价突破近 60 日高点")
        if 1.2 <= volume_ratio <= 3.5:
            score += 25
            reasons.append("成交量温和放大确认突破")
        if ret_20 > 0.03:
            score += 15
            reasons.append("短期动量同步改善")
        if drawdown > -0.2:
            score += 15

        if volume_ratio > 5:
            score -= 20
            risks.append("单日放量过度，可能是消息脉冲")
        if close < previous_high:
            risks.append("尚未形成有效突破")

        return _signal(
            self.name,
            symbol,
            market,
            score,
            close,
            holding_days=10,
            reasons=reasons,
            risks=risks,
            metrics={
                "previous_60d_high": previous_high,
                "volume_ratio": volume_ratio,
                "return_20d": ret_20,
                "max_drawdown_120d": drawdown,
            },
        )


class LowVolatilityRelativeStrengthStrategy(StrategyModule):
    name = "low_volatility_relative_strength"

    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        frame = _prepare(prices)
        close = float(frame.iloc[-1]["close"])
        ret_120 = _last(rate_of_change(frame["close"], 120))
        volatility = annualized_volatility(frame["close"].pct_change().dropna().tail(120))
        drawdown = max_drawdown(frame["close"].tail(120))
        score = 50 + ret_120 * 120 - volatility * 45 + max(drawdown, -0.5) * 40
        reasons = ["中期相对强度和低波动综合评分"]
        risks = []
        if volatility > 0.4:
            risks.append("波动率高于低波动策略偏好")
        if ret_120 < 0:
            risks.append("中期相对收益仍为负")
        return _signal(
            self.name,
            symbol,
            market,
            score,
            close,
            holding_days=30,
            reasons=reasons,
            risks=risks,
            metrics={
                "return_120d": ret_120,
                "volatility_120d": volatility,
                "max_drawdown_120d": drawdown,
            },
        )


class ControlledMeanReversionStrategy(StrategyModule):
    name = "controlled_mean_reversion"

    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        frame = _prepare(prices)
        close = float(frame.iloc[-1]["close"])
        ma60 = _last(moving_average(frame["close"], 60))
        ma120 = _last(moving_average(frame["close"], 120))
        drawdown_60 = close / float(frame["close"].tail(60).max()) - 1
        ret_5 = _last(rate_of_change(frame["close"], 5))
        distance_ma60 = close / ma60 - 1 if ma60 else 0

        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []
        if -0.18 <= drawdown_60 <= -0.05:
            score += 30
            reasons.append("回撤幅度适中，具备修复空间")
        if abs(distance_ma60) < 0.06:
            score += 25
            reasons.append("价格接近 60 日均线")
        if ret_5 > 0:
            score += 20
            reasons.append("短期出现企稳迹象")
        if close > ma120:
            score += 25
            reasons.append("长期趋势尚未破坏")
        else:
            risks.append("价格仍在长期均线下方")
        return _signal(
            self.name,
            symbol,
            market,
            score,
            close,
            holding_days=15,
            reasons=reasons,
            risks=risks,
            metrics={
                "drawdown_60d": drawdown_60,
                "distance_ma60": distance_ma60,
                "return_5d": ret_5,
                "ma60": ma60,
                "ma120": ma120,
            },
        )


class FundNavTrendStrategy(StrategyModule):
    name = "fund_nav_trend_drawdown"

    def evaluate(self, symbol: str, market: str, prices: pd.DataFrame) -> StrategySignal:
        frame = _prepare(prices)
        close = float(frame.iloc[-1]["close"])
        ret_60 = _last(rate_of_change(frame["close"], 60))
        ret_120 = _last(rate_of_change(frame["close"], 120))
        ma60 = _last(moving_average(frame["close"], 60))
        ma120 = _last(moving_average(frame["close"], 120))
        volatility = annualized_volatility(frame["close"].pct_change().dropna().tail(120))
        drawdown = max_drawdown(frame["close"].tail(120))

        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []
        if ret_60 > 0.05:
            score += 25
            reasons.append("近 60 日 NAV 趋势向好")
        if ret_120 > 0.08:
            score += 20
            reasons.append("近 120 日 NAV 中期动量占优")
        if close > ma60 > ma120:
            score += 25
            reasons.append("NAV 站上 60/120 日均线")
        if drawdown > -0.15:
            score += 15
            reasons.append("回撤可控，适合定投或趋势持有")
        if volatility < 0.25:
            score += 10
            reasons.append("净值波动较低")

        if drawdown < -0.25:
            score -= 20
            risks.append("基金阶段回撤较大")
        if ret_60 < 0:
            risks.append("近 60 日 NAV 仍为负增长")

        return _signal(
            self.name,
            symbol,
            market,
            score,
            close,
            holding_days=30,
            reasons=reasons,
            risks=risks,
            metrics={
                "return_60d": ret_60,
                "return_120d": ret_120,
                "ma60": ma60,
                "ma120": ma120,
                "volatility_120d": volatility,
                "max_drawdown_120d": drawdown,
            },
        )


def default_strategy_modules() -> list[StrategyModule]:
    return [
        TrendMomentumStrategy(),
        BreakoutVolumeStrategy(),
        LowVolatilityRelativeStrengthStrategy(),
        ControlledMeanReversionStrategy(),
        FundNavTrendStrategy(),
    ]


def _prepare(prices: pd.DataFrame) -> pd.DataFrame:
    frame = prices.dropna(subset=["close"]).sort_values("trade_date").copy()
    if len(frame) < 121:
        raise ValueError("strategy evaluation requires at least 121 price bars")
    if "high" not in frame:
        frame["high"] = frame["close"]
    if "volume" not in frame:
        frame["volume"] = 0
    return frame


def _last(series: pd.Series) -> float:
    value = series.dropna().iloc[-1]
    return float(value)


def _signal(
    strategy: str,
    symbol: str,
    market: str,
    score: float,
    close: float,
    holding_days: int,
    reasons: list[str],
    risks: list[str],
    metrics: dict[str, float | int | str | None],
) -> StrategySignal:
    bounded_score = max(0, min(100, round(score, 2)))
    action = "观察"
    if bounded_score >= 75:
        action = "强关注"
    elif bounded_score >= 60:
        action = "可观察"
    elif bounded_score < 40:
        action = "暂不考虑"
    confidence = "高" if bounded_score >= 75 else "中" if bounded_score >= 55 else "低"
    return StrategySignal(
        strategy=strategy,
        symbol=symbol,
        market=market,
        score=bounded_score,
        action=action,
        confidence=confidence,
        entry=round(close, 3),
        stop_loss=round(close * 0.92, 3),
        take_profit=round(close * 1.18, 3),
        holding_days=holding_days,
        reasons=reasons or ["暂无足够正向信号"],
        risks=risks or ["需结合大盘趋势和仓位纪律验证"],
        metrics={
            key: round(value, 4) if isinstance(value, float) else value
            for key, value in metrics.items()
        },
    )
