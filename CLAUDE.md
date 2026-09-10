# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

Two independent layers live in this repo:

1. **`twstock/`** — the upstream PyPI library (`twstock`, MIT, mlouielu/twstock): fetches Taiwan
   stock (TWSE/TPEX) price data and does simple analytics. Packaged, tested, released via CI.
2. **`agent/`** — a fork-local automated trading-signal agent built *on top of* the library
   (added on the `dev` branch; not part of the published package, has no packaging metadata, and
   is not covered by CI). Uses Traditional Chinese for all output and most comments.

Changes to `twstock/` should stay upstream-compatible (this is a fork of a public package).
`agent/` is local-only and can evolve freely.

## Commands

```bash
uv sync --group dev              # install deps (uv is the toolchain; Pipfile/flit.ini are vestigial)
uv run -m unittest               # run the library test suite (must be run from repo root)
uv run -m unittest test.test_stock                            # one module
uv run -m unittest test.test_stock.TWSEStockTest              # one class
uv run -m unittest test.test_stock.TWSEStockTest.test_fetch_31  # one test
uv run coverage run --source=twstock -m unittest              # what CI runs
```

Agent (never run by CI; needs `GEMINI_API_TOKEN` / `TELEGRAM_BOT_TOKEN` in the environment):

```bash
python agent/main.py             # daily scan → agent/report_YYYYMMDD.md + Telegram push
python agent/bot_daemon.py       # long-running Telegram command bot (polls getUpdates)
python agent/backtest.py 2330 12 # backtest one code over N months
python agent/test_entry_evaluator.py   # agent's only tests (unittest, standalone)
bash agent/run_daily.sh          # cron entry point; sources ~/.bashrc, logs to agent/cron.log
```

Note the agent scripts are run *as scripts from the repo root*, not as a package — they
`sys.path.insert` the repo root and then import each other by flat module name
(`from db_utils import ...`), so `python -m agent.main` will not work.

## Library architecture (`twstock/`)

- **Fetcher layer** (`stock.py`): `BaseFetcher` → `TWSEFetcher` / `TPEXFetcher`. Each hits a
  different JSON endpoint with a different date/field layout, and normalizes rows into the shared
  `DATATUPLE` namedtuple (`date, capacity, turnover, open, high, low, close, change, transaction`).
  Both retry (default 5) and both are ROC-calendar aware (`_convert_date`).
- **`Stock`** is a thin object over a `data: list[DATATUPLE]` plus lazy `@property` column views
  (`.price`, `.high`, `.capacity`, …). Which fetcher it gets is decided by the stock-code database,
  unless `force_data_source='twse'|'tpex'` is passed. `initial_fetch=False` yields an empty `Stock`
  you can fill by assigning `.data` — this is how the agent injects DB-cached rows.
- **`Analytics`** (`analytics.py`) is a **mixin that `Stock` inherits**, so `stock.moving_average(...)`
  works directly. `BestFourPoint` wraps a `Stock` and implements the "四大買賣點" rules.
  `legacy.py` holds an unused port of toomore/grs analytics.
- **Stock code DB** (`codes/`): shipped CSVs (`twse_equities.csv`, `tpex_equities.csv`) parsed at
  import into the module-level `codes` dict. `twstock.__update_codes()` (CLI `twstock -U`) refetches
  them from isin.twse.com.tw and **overwrites the files inside the installed package**.
  A code missing from these CSVs raises `StockIDNotFoundError` at `Stock()` construction.
- **Proxy layer** (`proxy.py`): all HTTP goes through `proxy.get_session()`, which installs a
  `_LegacyCertAdapter` (TWSE needs legacy SSL renegotiation). Provider is a global singleton set via
  `configure_proxy_provider()` — remember `reset_proxy_provider()` in tests.
- **`realtime.py`** parses the terse `msgArray` field codes (`z`=price, `v`=volume, `a`/`b`=best
  ask/bid ladders, …) into readable dicts; `mock/` holds captured payloads for tests.

**TWSE rate limit: 3 requests per 5 seconds, or you get banned.** Any new loop over months or codes
must sleep (the agent uses `time.sleep(3.0)` between month fetches, `1.0` between stocks).

### Tests

`unittest` + **vcrpy** with `record_mode="none"` and `cassette_library_dir="test/cassettes"`.
Tests never hit the network; adding a test that needs new HTTP means recording a new cassette
(temporarily switch record mode, then set it back). Cassette paths are relative to the repo root,
which is why tests must be run from there.

## Agent architecture (`agent/`)

Data flow for a daily run (`main.py`):

```
config.json watchlist
  → db_utils.get_cached_stock(code, …)   # SQLite-backed Stock, fetches only missing months
  → EntryEvaluator(stock).evaluate()     # quantitative verdict dict
  → gemini_utils.get_gemini_insight(…)   # optional LLM commentary (Gemini 2.5 Flash, raw requests)
  → generate_markdown_report()  → agent/report_YYYYMMDD.md
  → generate_telegram_report()  → telegram_utils.send_telegram_message()
```

- **`db_utils.py`** owns `agent/twstock_cache.db` (SQLite, WAL, `timeout=10` because the daemon and
  the cron job contend for it). `daily_prices` is the price cache: `get_cached_stock` fetches from
  TWSE only for months with no rows — **except the current month, which is always refetched**.
  `get_offline_stock` is the zero-network path used by the Telegram bot for fast replies.
  `portfolio` holds positions, but `get_open_positions()` calls `sync_portfolio_from_json()` first,
  which **deletes all OPEN rows and re-inserts from `agent/portfolio.json`** — so `portfolio.json`
  is the source of truth for holdings and `record_buy`/`record_sell` writes to OPEN rows are
  transient. Edit `portfolio.json`, not the table.
- **`entry_evaluator.py`** is the decision core. `EntryEvaluator.evaluate()` scores 0–100 across
  trend/MA (40) + momentum (30) + risk-reward (30), applies red-flag vetoes, and returns a dict
  whose keys (`can_enter`, `verdict`, `verdict_badge`, `score`, `rrr`, `stop_loss`, `signals`,
  `red_flags`, `reasons`, …) are consumed by the report generators, the Gemini prompt, and the bot.
  The full contract is documented in the `evaluate()` docstring — keep it in sync when adding keys.
  It needs ≥20 days of data (hence the 120-day fetch window in `main.py`, which also covers MA60).
  `MarketRegimeEvaluator` aggregates all per-stock evals into a market-breadth verdict.
- **Indicators**: `macd.py` and `tech_indicators.py` (RSI/KD/ATR) are pure-list functions, no pandas
  or numpy anywhere in this repo. `StrategyEngine` in `main.py` is the older per-strategy signal
  aggregator, still used by `bot_daemon.py`.
- **`bot_daemon.py`** long-polls Telegram `getUpdates` and rejects any chat id other than
  `config.json:telegram_chat_id` — that check is the only access control, keep it.
  Commands: `/action` `/top` `/alerts` `/portfolio` `/analyze <code>` `/list` `/add` `/remove`.
- Config is plain JSON edited in place: `config.json` (watchlist + chat id, written back by
  `/add`/`/remove`) and `portfolio.json`. Secrets come only from env vars.
- `agent/report_*.md`, `agent/*.log`, and `*.db` are gitignored — generated output, don't commit.
