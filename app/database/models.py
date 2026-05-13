from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

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

    __table_args__ = (UniqueConstraint("asset_id", "trade_date", "adjust_type", name="uq_price_daily"),)


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
