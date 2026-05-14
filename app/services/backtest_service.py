import pandas as pd
from sqlalchemy.orm import Session

from app.database.models import AssetType, Market
from app.domain.backtest import BacktestRequest, BacktestResult, BacktestTrade
from app.domain.errors import NoMarketDataError
from app.indicators.risk import max_drawdown
from app.indicators.technical import moving_average
from app.repositories.assets import AssetRepository
from app.repositories.backtests import BacktestRepository
from app.services.price_service import PriceService, normalize_hk_symbol


class BacktestService:
    def __init__(self, session: Session, price_service: PriceService | None = None):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.assets = AssetRepository(session)
        self.backtests = BacktestRepository(session)

    def run_moving_average_cross(self, request: BacktestRequest) -> BacktestResult:
        prices = self._load_prices(request)
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

    def _load_prices(self, request: BacktestRequest) -> pd.DataFrame:
        if request.market == Market.HK.value:
            return self.price_service.get_hk_stock_history(request.symbol)
        return self.price_service.get_a_share_history(request.symbol)

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
