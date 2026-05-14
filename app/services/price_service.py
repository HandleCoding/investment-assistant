from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data_sources.akshare_client import AkShareClient
from app.data_sources.normalizers import (
    normalize_a_share_prices,
    normalize_a_share_tx_prices,
    normalize_hk_daily_prices,
    price_bars_to_frame,
)
from app.database.models import Asset, AssetType, Market, PriceDaily
from app.domain.errors import DataSourceError, NoMarketDataError
from app.domain.market_data import PriceBar


class PriceService:
    def __init__(self, session: Session, data_client: AkShareClient | None = None) -> None:
        self.session = session
        self.data_client = data_client or AkShareClient()

    def get_a_share_history(
        self,
        symbol: str,
        lookback_days: int = 420,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        asset = self._get_or_create_asset(
            symbol=symbol,
            market=Market.A_SHARE,
            asset_type=AssetType.STOCK,
        )
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        cached_bars = self._list_cached_prices(asset.id, start_date, adjust)
        if not cached_bars or cached_bars[-1].trade_date < end_date - timedelta(days=3):
            fetched_bars = self._fetch_a_share_bars(symbol, start_date, end_date, adjust)
            if not fetched_bars:
                raise NoMarketDataError(f"未获取到 {symbol} 的 A 股行情数据。")
            self._upsert_prices(asset.id, fetched_bars, adjust)
            cached_bars = self._list_cached_prices(asset.id, start_date, adjust)

        if not cached_bars:
            raise NoMarketDataError(f"本地没有 {symbol} 的可用 A 股行情数据。")

        return price_bars_to_frame(cached_bars)

    def get_hk_stock_history(
        self,
        symbol: str,
        lookback_days: int = 420,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        normalized_symbol = normalize_hk_symbol(symbol)
        asset = self._get_or_create_asset(
            symbol=normalized_symbol,
            market=Market.HK,
            asset_type=AssetType.STOCK,
        )
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        cached_bars = self._list_cached_prices(asset.id, start_date, adjust)
        if not cached_bars or cached_bars[-1].trade_date < end_date - timedelta(days=3):
            raw_prices = self.data_client.fetch_hk_stock_daily_sina(normalized_symbol, adjust)
            fetched_bars = [
                bar
                for bar in normalize_hk_daily_prices(raw_prices)
                if start_date <= bar.trade_date <= end_date
            ]
            if not fetched_bars:
                raise NoMarketDataError(f"未获取到 {normalized_symbol} 的港股行情数据。")
            self._upsert_prices(asset.id, fetched_bars, adjust)
            cached_bars = self._list_cached_prices(asset.id, start_date, adjust)

        if not cached_bars:
            raise NoMarketDataError(f"本地没有 {normalized_symbol} 的可用港股行情数据。")

        return price_bars_to_frame(cached_bars)

    def _fetch_a_share_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> list[PriceBar]:
        try:
            raw_prices = self.data_client.fetch_a_share_history(
                symbol,
                start_date,
                end_date,
                adjust,
            )
            return normalize_a_share_prices(raw_prices)
        except DataSourceError as primary_error:
            try:
                raw_prices = self.data_client.fetch_a_share_history_tx(
                    symbol,
                    start_date,
                    end_date,
                    adjust,
                )
                return normalize_a_share_tx_prices(raw_prices)
            except DataSourceError as fallback_error:
                message = f"{primary_error}；备用腾讯源也失败：{fallback_error}"
                raise DataSourceError(message) from fallback_error

    def _get_or_create_asset(self, symbol: str, market: Market, asset_type: AssetType) -> Asset:
        statement = select(Asset).where(Asset.symbol == symbol, Asset.market == market.value)
        asset = self.session.scalar(statement)
        if asset is not None:
            return asset

        asset = Asset(symbol=symbol, name=None, market=market.value, asset_type=asset_type.value)
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def _list_cached_prices(self, asset_id: int, start_date: date, adjust: str) -> list[PriceBar]:
        statement = (
            select(PriceDaily)
            .where(
                PriceDaily.asset_id == asset_id,
                PriceDaily.trade_date >= start_date,
                PriceDaily.adjust_type == adjust,
            )
            .order_by(PriceDaily.trade_date)
        )
        rows = self.session.scalars(statement).all()
        return [
            PriceBar(
                trade_date=row.trade_date,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
                amount=row.amount,
                turnover_rate=row.turnover_rate,
                pct_change=row.pct_change,
            )
            for row in rows
        ]

    def _upsert_prices(self, asset_id: int, price_bars: list[PriceBar], adjust: str) -> None:
        existing_dates = set(
            self.session.scalars(
                select(PriceDaily.trade_date).where(
                    PriceDaily.asset_id == asset_id,
                    PriceDaily.adjust_type == adjust,
                )
            ).all()
        )
        for bar in price_bars:
            if bar.trade_date in existing_dates:
                continue
            self.session.add(
                PriceDaily(
                    asset_id=asset_id,
                    trade_date=bar.trade_date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    amount=bar.amount,
                    turnover_rate=bar.turnover_rate,
                    pct_change=bar.pct_change,
                    adjust_type=adjust,
                )
            )
        self.session.commit()


def normalize_hk_symbol(symbol: str) -> str:
    return symbol.upper().removeprefix("HK").zfill(5)
