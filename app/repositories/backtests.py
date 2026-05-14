import json

from sqlalchemy.orm import Session

from app.database.models import BacktestRun
from app.domain.backtest import BacktestResult


class BacktestRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_result(self, asset_id: int, strategy_name: str, result: BacktestResult) -> BacktestRun:
        run = BacktestRun(
            asset_id=asset_id,
            strategy_name=strategy_name,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_cash=result.initial_cash,
            final_value=result.final_value,
            total_return=result.total_return,
            max_drawdown=result.max_drawdown,
            trade_count=result.trade_count,
            win_rate=result.win_rate,
            trades_json=json.dumps([trade.__dict__ for trade in result.trades], default=str),
        )
        self.session.add(run)
        self.session.flush()
        return run
