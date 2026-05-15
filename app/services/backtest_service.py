import pandas as pd
from sqlalchemy.orm import Session

from app.database.models import AssetType, Market
from app.domain.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestTrade,
    SignalBacktestRequest,
)
from app.domain.errors import NoMarketDataError
from app.indicators.risk import max_drawdown
from app.indicators.technical import moving_average
from app.repositories.assets import AssetRepository
from app.repositories.backtests import BacktestRepository
from app.services.price_service import PriceService, normalize_hk_symbol
from app.strategies.modules import default_strategy_modules


class BacktestService:
    def __init__(self, session: Session, price_service: PriceService | None = None):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.assets = AssetRepository(session)
        self.backtests = BacktestRepository(session)

    def run_moving_average_cross(self, request: BacktestRequest) -> BacktestResult:
        prices = self._load_prices(request.symbol, request.market)
        if prices.empty:
            raise NoMarketDataError(f"No price data for {request.symbol}")

        prices = prices.sort_values("trade_date").copy()
        if request.start_date:
            prices = prices[prices["trade_date"] >= request.start_date]
        if request.end_date:
            prices = prices[prices["trade_date"] <= request.end_date]
        if len(prices) < request.slow_window + 2:
            raise NoMarketDataError("Not enough market data for backtest window")

        prices["fast_ma"] = moving_average(prices["close"], request.fast_window)
        prices["slow_ma"] = moving_average(prices["close"], request.slow_window)
        result = self._simulate(prices.dropna(subset=["fast_ma", "slow_ma"]), request)
        self._persist(request, result)
        self.session.commit()
        return result

    def run_signal_holding_period(self, request: SignalBacktestRequest) -> BacktestResult:
        prices = self._load_prices(request.symbol, request.market).sort_values("trade_date").copy()
        if len(prices) < 140:
            raise NoMarketDataError("Not enough market data for signal backtest")

        strategy = next(
            item for item in default_strategy_modules() if item.name == request.strategy_name
        )
        cash = request.initial_cash
        quantity = 0.0
        trades: list[BacktestTrade] = []
        equity_values = []
        winning_trades = 0
        closed_trades = 0
        index = 121
        while index + request.holding_days < len(prices):
            window = prices.iloc[:index].copy()
            signal = strategy.evaluate(request.symbol, request.market, window)
            entry_price = float(prices.iloc[index]["close"])
            exit_index = index + request.holding_days
            exit_price = float(prices.iloc[exit_index]["close"])
            if signal.score >= 60:
                quantity = cash / entry_price
                cash = 0
                trades.append(
                    BacktestTrade(
                        prices.iloc[index]["trade_date"],
                        "BUY",
                        entry_price,
                        quantity,
                        cash,
                    )
                )
                cash = quantity * exit_price
                trades.append(
                    BacktestTrade(
                        prices.iloc[exit_index]["trade_date"],
                        "SELL",
                        exit_price,
                        quantity,
                        cash,
                    )
                )
                if exit_price > entry_price:
                    winning_trades += 1
                closed_trades += 1
                quantity = 0
            equity_values.append(cash)
            index += request.rebalance_days

        final_value = cash + quantity * float(prices.iloc[-1]["close"])
        result = BacktestResult(
            symbol=request.symbol,
            market=request.market,
            start_date=prices.iloc[121]["trade_date"],
            end_date=prices.iloc[min(index, len(prices) - 1)]["trade_date"],
            initial_cash=request.initial_cash,
            final_value=round(final_value, 2),
            total_return=round(final_value / request.initial_cash - 1, 4),
            max_drawdown=round(max_drawdown(pd.Series(equity_values or [request.initial_cash])), 4),
            trade_count=len(trades),
            win_rate=round(winning_trades / closed_trades, 4) if closed_trades else 0,
            trades=trades,
        )
        self._persist_signal(request, result)
        self.session.commit()
        return result

    def _load_prices(self, symbol: str, market: str) -> pd.DataFrame:
        if market == Market.HK.value:
            return self.price_service.get_hk_stock_history(symbol)
        if market == Market.FUND.value:
            return self.price_service.get_fund_nav_history(symbol)
        return self.price_service.get_a_share_history(symbol)

    def _simulate(self, prices: pd.DataFrame, request: BacktestRequest) -> BacktestResult:
        cash = request.initial_cash
        quantity = 0.0
        entry_price = 0.0
        winning_trades = 0
        closed_trades = 0
        trades: list[BacktestTrade] = []
        equity_values = []
        previous_signal = False

        for row in prices.itertuples(index=False):
            signal = row.fast_ma > row.slow_ma
            price = float(row.close)
            trade_date = row.trade_date
            if signal and not previous_signal and cash > 0:
                quantity = cash / price
                cash = 0
                entry_price = price
                trades.append(BacktestTrade(trade_date, "BUY", price, round(quantity, 4), cash))
            elif not signal and previous_signal and quantity > 0:
                cash = quantity * price
                if price > entry_price:
                    winning_trades += 1
                closed_trades += 1
                trades.append(BacktestTrade(trade_date, "SELL", price, round(quantity, 4), cash))
                quantity = 0
            equity_values.append(cash + quantity * price)
            previous_signal = signal

        last_row = prices.iloc[-1]
        final_value = cash + quantity * float(last_row["close"])
        total_return = final_value / request.initial_cash - 1
        drawdown = max_drawdown(pd.Series(equity_values))
        win_rate = winning_trades / closed_trades if closed_trades else 0
        return BacktestResult(
            symbol=request.symbol,
            market=request.market,
            start_date=prices.iloc[0]["trade_date"],
            end_date=prices.iloc[-1]["trade_date"],
            initial_cash=request.initial_cash,
            final_value=round(final_value, 2),
            total_return=round(total_return, 4),
            max_drawdown=round(drawdown, 4),
            trade_count=len(trades),
            win_rate=round(win_rate, 4),
            trades=trades,
        )

    def _persist(self, request: BacktestRequest, result: BacktestResult) -> None:
        symbol = (
            normalize_hk_symbol(request.symbol)
            if request.market == Market.HK.value
            else request.symbol
        )
        asset = self.assets.get_or_create(symbol, request.market, AssetType.STOCK.value, symbol)
        self.backtests.save_result(asset.id, "MA_CROSS", result)

    def _persist_signal(self, request: SignalBacktestRequest, result: BacktestResult) -> None:
        symbol = (
            normalize_hk_symbol(request.symbol)
            if request.market == Market.HK.value
            else request.symbol
        )
        asset_type = (
            AssetType.FUND.value
            if request.market == Market.FUND.value
            else AssetType.STOCK.value
        )
        asset = self.assets.get_or_create(symbol, request.market, asset_type, symbol)
        self.backtests.save_result(asset.id, f"SIGNAL_{request.strategy_name}", result)
