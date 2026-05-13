# Personal Investment Assistant Plan

## 1. Product Positioning

Build a personal investment research assistant for A-share decision support, with fund analysis as a first-class capability and Hong Kong stock support as an extension.

The system should not promise returns or act as an automatic trading engine. Its purpose is to make investment decisions more structured, comparable, and reviewable.

Primary goals:

- Analyze A-share stocks, funds, ETFs, and selected Hong Kong stocks.
- Generate structured research reports from a stock or fund code.
- Provide scoring, risk warnings, and watchlist suggestions.
- Support backtesting for buy/sell rules before real use.
- Track personal positions, original buy reasons, and exit conditions.

The user's aggressive reference target is 10% monthly return, but the system should optimize for risk-adjusted decision quality rather than chasing this target directly.

## 2. Recommended Stack

MVP stack:

- Python
- FastAPI
- SQLite
- SQLAlchemy
- AkShare
- pandas
- numpy
- Plotly or ECharts for charts
- APScheduler for local scheduled jobs
- pytest for tests

Future options:

- PostgreSQL when data volume or concurrent writes grow.
- Celery or RQ when scheduled jobs become heavier.
- React, Vue, or Next.js when the UI needs to become a full web app.
- vectorbt or backtrader when backtesting becomes more complex.

The project should keep database access behind SQLAlchemy so SQLite can be replaced with PostgreSQL later.

## 3. Architecture Principles

Keep the architecture simple, layered, and extensible:

- `api`: HTTP route layer only.
- `services`: business use cases and orchestration.
- `domain`: domain models, enums, and decision objects.
- `indicators`: technical, risk, valuation, and fund calculations.
- `data_sources`: external data clients such as AkShare.
- `database`: persistence models, sessions, and repositories.
- `core`: configuration, logging, and shared infrastructure.
- `scripts`: local data update or maintenance commands.
- `tests`: unit tests for indicators, scoring, and backtesting.

Rules:

- Do not put data-fetching logic in API routes.
- Do not put scoring rules directly in database models.
- Keep indicators as pure functions where possible.
- Keep AkShare-specific field normalization in `data_sources`.
- Make analysis reports reproducible from stored data.
- Prefer explicit, readable rules over premature machine learning.

## 4. Data Scope

### A-shares

First-priority market.

Data to support:

- Basic stock information.
- Daily, weekly, and monthly price data.
- Forward-adjusted historical prices.
- Volume, turnover, amount, and percentage change.
- Valuation metrics such as PE, PB, PS, market cap, and dividend yield where available.
- Financial metrics such as revenue, net profit, ROE, margins, debt ratio, and operating cash flow.
- Industry classification.
- Index data such as CSI 300, CSI 500, ChiNext, and STAR 50.

### Funds and ETFs

First-class support after stock MVP.

Data to support:

- Fund basic information.
- Historical net value.
- Stage returns.
- Maximum drawdown.
- Volatility.
- Sharpe ratio.
- Fund manager information.
- Fund size and fees.
- Holdings and industry concentration where available.
- ETF price, volume, amount, premium/discount, and tracking index where available.

### Hong Kong Stocks

Second-stage support.

Data to support initially:

- Code lookup.
- Historical prices.
- Trend analysis.
- Volatility.
- Maximum drawdown.
- Liquidity filter.
- Basic valuation if reliable data is available.

Hong Kong stocks should initially support input-code analysis, not broad-market recommendation.

## 5. Database Design

Start with SQLite and keep the schema portable.

Initial tables:

### assets

Stores all analyzable assets.

Fields:

- id
- symbol
- name
- market: A_SHARE, HK, FUND, ETF, INDEX
- asset_type: STOCK, FUND, ETF, INDEX
- industry
- status
- created_at
- updated_at

### price_daily

Stores stock, ETF, index, and Hong Kong daily prices.

Fields:

- id
- asset_id
- trade_date
- open
- high
- low
- close
- volume
- amount
- turnover_rate
- pct_change
- adjust_type

### fund_nav_daily

Stores fund net value history.

Fields:

- id
- asset_id
- nav_date
- unit_nav
- accumulated_nav
- daily_return

### stock_financial_metrics

Stores periodic stock financial metrics.

Fields:

- id
- asset_id
- report_date
- revenue
- net_profit
- roe
- gross_margin
- debt_ratio
- operating_cashflow
- eps

### valuation_metrics

Stores valuation snapshots.

Fields:

- id
- asset_id
- trade_date
- pe
- pb
- ps
- dividend_yield
- market_cap

### analysis_reports

Stores generated analysis results.

Fields:

- id
- asset_id
- report_date
- score_total
- score_fundamental
- score_valuation
- score_technical
- score_momentum
- score_risk
- conclusion
- reasons_json

### watchlist

Stores personal watchlist entries.

Fields:

- id
- asset_id
- group_name
- target_price
- note

### portfolio_positions

Stores manually entered positions.

Fields:

- id
- asset_id
- quantity
- cost_price
- buy_date
- strategy_tag
- buy_reason
- exit_condition

## 6. Analysis Report

For an input stock code, generate a structured report:

- Basic information.
- Current price and recent return.
- Trend analysis.
- Valuation analysis.
- Financial quality.
- Risk analysis.
- Bull case.
- Bear case.
- Trigger conditions for entry.
- Trigger conditions for exit.
- Overall score.
- Decision label.

Decision labels:

- Strong Watch
- Watch
- Neutral
- High Risk
- Avoid

The system should avoid absolute wording such as "must buy" or "guaranteed return".

## 7. Stock Scoring Model

Use a transparent 100-point rule-based model in the first version.

Suggested weights:

- Fundamental quality: 25
- Valuation: 20
- Trend: 20
- Liquidity and volume: 15
- Risk: 20

Suggested interpretation:

- 85-100: strong watch, but still use position control.
- 70-84: watch, wait for a better entry.
- 55-69: neutral, no urgency.
- 40-54: high risk.
- 0-39: avoid.

The score is a comparison and discipline tool, not a return forecast.

## 8. Fund Scoring Model

Suggested weights:

- Long-term return: 25
- Drawdown control: 25
- Fund manager quality: 20
- Holding quality and concentration: 15
- Fees, size, and liquidity: 15

Suggested labels:

- Suitable for regular investment.
- Worth watching.
- High volatility.
- Style drift risk.
- Avoid.

## 9. Candidate Screening

Call this feature a candidate pool, not direct recommendation.

Initial A-share filters:

- Price above long-term moving average.
- 20-day moving average above 60-day moving average.
- Current valuation not at extreme historical high.
- Liquidity above threshold.
- Exclude ST and delisting-risk names.
- Recent drawdown within acceptable range.

Initial fund filters:

- 1-year return in top 30% of category.
- Maximum drawdown better than category median.
- Manager tenure above 2 years.
- Fund size within a reasonable range.
- Sharpe ratio above category median.

Output should include both positive and negative reasons.

## 10. Backtesting

Backtesting is required before trusting a rule.

Initial inputs:

- Asset universe.
- Buy conditions.
- Sell conditions.
- Holding period.
- Rebalance frequency.
- Position sizing.
- Fee rate.
- Slippage assumption.

Initial outputs:

- Total return.
- Annualized return.
- Monthly returns.
- Maximum drawdown.
- Win rate.
- Profit/loss ratio.
- Sharpe ratio.
- Worst month.
- Consecutive loss count.
- Benchmark comparison.

First strategies to implement:

1. Moving-average trend strategy.
2. Low-valuation reversal strategy.
3. Momentum strategy.
4. Fund regular-investment strategy.

Backtesting constraints:

- Do not use future data.
- Use financial metrics only after realistic disclosure dates.
- Include fees and slippage.
- Test across bull, bear, and sideways markets.
- Do not only test successful examples.

## 11. Portfolio And Risk Control

Manual position tracking is important for personal use.

Track:

- Asset code.
- Quantity.
- Cost price.
- Buy date.
- Buy reason.
- Strategy tag.
- Planned exit condition.

Daily or on-demand analysis:

- Total portfolio return.
- Monthly return.
- Year-to-date return.
- Maximum drawdown.
- Per-position PnL.
- Industry exposure.
- Fund holding overlap with stock positions where data is available.
- Triggered stop-loss or take-profit conditions.
- Whether original buy reason still holds.

Suggested risk rules:

- Single stock position no more than 10-15% initially.
- Single fund position no more than 20-30% initially.
- Single industry exposure no more than 30-40% initially.
- Re-evaluate every position when the original buy reason breaks.
- Separate short-term, swing, and long-term strategies.

## 12. Pages

Initial pages:

1. Dashboard
   - Portfolio summary.
   - Market snapshot.
   - Watchlist alerts.
   - Recent signals.

2. Asset Analysis
   - Code input.
   - Generated report.
   - Price chart.
   - Indicators.
   - Score breakdown.

3. Candidate Pool
   - Stock candidates.
   - Fund candidates.
   - ETF candidates.
   - Filter controls.

4. Backtesting
   - Strategy selection.
   - Parameter input.
   - Equity curve.
   - Metrics.

5. Portfolio
   - Manual position entry.
   - PnL.
   - Exposure.
   - Alerts.

6. Data Management
   - Manual data refresh.
   - Data freshness.
   - Cache cleanup.

## 13. Delivery Roadmap

### Phase 0: Requirement narrowing, 1-2 days

Decide:

- Preferred holding period.
- Maximum acceptable monthly loss.
- Main asset types.
- Daily monitoring willingness.
- Desired strictness of decision labels.

Default assumption:

- Swing to medium-term style.
- Holding period from 2 weeks to 3 months.
- A-share, ETF, and fund first.
- Hong Kong stocks by input-code analysis only.

### Phase 1: MVP, 1-2 weeks

Deliver:

- Project setup.
- AkShare integration.
- SQLite storage.
- A-share code input.
- Historical price cache.
- Basic indicators.
- Risk metrics.
- Rule-based score.
- Structured report.

### Phase 2: Fund and ETF analysis, 1 week

Deliver:

- Fund net value history.
- Stage returns.
- Drawdown.
- Volatility.
- Sharpe ratio.
- ETF trend and liquidity analysis.
- Fund/ETF score.

### Phase 3: Backtesting, 1-2 weeks

Deliver:

- Single-asset backtest.
- Stock-pool backtest.
- Fund regular-investment backtest.
- Fees and slippage.
- Return curve and metrics.
- Benchmark comparison.

### Phase 4: Candidate pool and scheduled updates, 1 week

Deliver:

- Watchlist refresh.
- Candidate generation.
- Daily data updates.
- Risk alerts.

### Phase 5: Portfolio assistant, 1 week

Deliver:

- Manual position tracking.
- Buy reason and exit condition tracking.
- Portfolio return and drawdown.
- Exposure analysis.
- Triggered condition alerts.

### Phase 6: Enhancements, ongoing

Possible additions:

- Financial statement quality analysis.
- Industry momentum.
- Announcement and news summarization.
- Northbound capital flow.
- Dragon Tiger List.
- AH premium.
- Historical valuation percentile.
- Market regime detection.
- LLM-generated natural-language report.

## 14. First Implementable Version

Build only these first:

1. Input A-share code and fetch historical prices.
2. Store price history in SQLite.
3. Calculate moving averages, recent returns, volatility, and maximum drawdown.
4. Generate a 0-100 score.
5. Show a structured analysis report.
6. Cache results to reduce repeated AkShare calls.

Then add:

1. Fund code analysis.
2. Hong Kong stock code analysis.
3. First moving-average backtest.

## 15. Quality Bar

Code quality expectations:

- Keep modules small and focused.
- Prefer pure functions for indicators.
- Keep business rules readable and testable.
- Add tests for calculations and scoring rules.
- Avoid unnecessary abstractions.
- Avoid hidden data mutations.
- Normalize external data at the boundary.
- Keep API responses stable and explicit.

Investment quality expectations:

- Always show both upside and downside reasons.
- Always show risk metrics with return metrics.
- Prefer position sizing suggestions over binary buy/sell calls.
- Never hide assumptions.
- Do not optimize only for monthly return.
- Treat backtest results as filtering evidence, not proof of future profit.
