# Investment Assistant

Personal investment research assistant for A-shares, funds, ETFs, and selected Hong Kong stocks.

## Goals

- Generate structured analysis reports from asset codes.
- Cache market data locally with SQLite.
- Score assets with transparent, rule-based models.
- Backtest buy/sell rules before real use.
- Track personal positions and risk conditions.

See `plan.md` for the full roadmap.

## Development

This project uses `uv` for local environment and dependency management.

```bash
uv sync --extra dev
source .venv/bin/activate
uvicorn app.main:app --reload
```

PyCharm interpreter path:

```text
.venv/bin/python
```

## Project Layout

```text
app/api          HTTP routes
app/core         configuration and shared infrastructure
app/data_sources external market data clients
app/database     persistence layer
app/domain       domain types and schemas
app/indicators   pure calculation functions
app/services     business use cases
scripts          local maintenance scripts
tests            automated tests
```
