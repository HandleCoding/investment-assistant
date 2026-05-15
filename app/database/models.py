from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Market(StrEnum):
    A_SHARE = "A_SHARE"
    HK = "HK"
    FUND = "FUND"
    ETF = "ETF"
    INDEX = "INDEX"


class AssetType(StrEnum):
    STOCK = "STOCK"
    FUND = "FUND"
    ETF = "ETF"
    INDEX = "INDEX"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str | None] = mapped_column(String(128))
    market: Mapped[str] = mapped_column(String(32), index=True)
    asset_type: Mapped[str] = mapped_column(String(32), index=True)
    industry: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    prices: Mapped[list["PriceDaily"]] = relationship(back_populates="asset")

    __table_args__ = (UniqueConstraint("symbol", "market", name="uq_asset_symbol_market"),)


class PriceDaily(Base):
    __tablename__ = "price_daily"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    amount: Mapped[float | None] = mapped_column(Float)
    turnover_rate: Mapped[float | None] = mapped_column(Float)
    pct_change: Mapped[float | None] = mapped_column(Float)
    adjust_type: Mapped[str] = mapped_column(String(16), default="qfq")

    asset: Mapped[Asset] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint("asset_id", "trade_date", "adjust_type", name="uq_price_daily"),
    )


class FundNavDaily(Base):
    __tablename__ = "fund_nav_daily"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    nav_date: Mapped[date] = mapped_column(Date, index=True)
    unit_nav: Mapped[float | None] = mapped_column(Float)
    accumulated_nav: Mapped[float | None] = mapped_column(Float)
    daily_return: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("asset_id", "nav_date", name="uq_fund_nav_daily"),)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    score_total: Mapped[float | None] = mapped_column(Float)
    score_fundamental: Mapped[float | None] = mapped_column(Float)
    score_valuation: Mapped[float | None] = mapped_column(Float)
    score_technical: Mapped[float | None] = mapped_column(Float)
    score_momentum: Mapped[float | None] = mapped_column(Float)
    score_risk: Mapped[float | None] = mapped_column(Float)
    conclusion: Mapped[str | None] = mapped_column(String(64))
    reasons_json: Mapped[str | None] = mapped_column(Text)


class CandidateEntry(Base):
    __tablename__ = "candidate_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    generated_at: Mapped[date] = mapped_column(Date, index=True)
    score: Mapped[float] = mapped_column(Float)
    conclusion: Mapped[str] = mapped_column(String(64))
    return_20d: Mapped[float | None] = mapped_column(Float)
    max_drawdown: Mapped[float | None] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(Text)
    risk: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="WATCHING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    asset: Mapped[Asset] = relationship()

    __table_args__ = (
        UniqueConstraint("asset_id", "generated_at", name="uq_candidate_asset_generated_at"),
    )


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    cost_price: Mapped[float] = mapped_column(Float)
    last_price: Mapped[float | None] = mapped_column(Float)
    stop_loss_price: Mapped[float | None] = mapped_column(Float)
    take_profit_price: Mapped[float | None] = mapped_column(Float)
    opened_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    asset: Mapped[Asset] = relationship()

    __table_args__ = (UniqueConstraint("asset_id", "status", name="uq_open_position_asset_status"),)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    strategy_name: Mapped[str] = mapped_column(String(64))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    initial_cash: Mapped[float] = mapped_column(Float)
    final_value: Mapped[float] = mapped_column(Float)
    total_return: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    trade_count: Mapped[int] = mapped_column(Integer)
    win_rate: Mapped[float] = mapped_column(Float)
    trades_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    asset: Mapped[Asset] = relationship()


class TradeRecord(Base):
    __tablename__ = "trade_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    action: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    asset: Mapped[Asset] = relationship()
