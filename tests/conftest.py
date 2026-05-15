import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import (
    Asset,
    BacktestRun,
    CandidateEntry,
    FundNavDaily,
    PortfolioPosition,
    PriceDaily,
    TradeRecord,
)
from app.database.session import Base


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Asset.__table__,
            PriceDaily.__table__,
            FundNavDaily.__table__,
            CandidateEntry.__table__,
            PortfolioPosition.__table__,
            BacktestRun.__table__,
            TradeRecord.__table__,
        ],
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        yield session
