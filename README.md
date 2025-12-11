# Currently moved to 
[here](https://github.com/OvooLab/AgenticTrade)
In Progress, yet private repo with other project members

# Auto-Trade (Hyperliquid)

Modular scaffold for an automated trading service on Hyperliquid. The goal is to keep concerns separated: data collection, prompt construction, LLM decisioning, risk checks, and order execution.

## Project layout
- `src/utils.py`: existing helper for Hyperliquid auth/bootstrap via `config.json`.
- `src/config/settings.py`: app, LLM, news, and risk settings loaders.
- `src/clients/`: Hyperliquid and news clients.
- `src/data/`: market/news services plus shared data models.
- `src/agent/`: prompt builder, schema, and LLM client stub.
- `src/trading/`: risk manager and trade executor.
- `src/services/decision_loop.py`: orchestrates fetch → decide → execute.
- `src/runner.py`: entrypoint wiring everything together.
- `src/data/market_parser.py`: indicator calculations (EMA, MACD, RSI, ATR) and parsed snapshot builder.
- `src/data/account_service.py`: fetch current account state, margin, and open positions.
- `src/agent/prompt_builder.py`: structured prompt helpers plus a demo prompt mixer for market + account state.
- `.env.example`: environment variable template (copy to `.env`).
- `config.example.json`: Hyperliquid key/address template (copy to `config.json`).

## How it works
1. `HyperliquidClient` uses `src.utils.setup` to authenticate and provides market data + order calls.
2. `MarketDataService` aggregates candles/metrics; `NewsService` (placeholder) pulls headlines.
3. `prompt_builder` shapes data into a prompt payload for the `LLMClient`.
4. `LLMClient` (stub) returns a structured `LLMDecision`; `RiskManager` enforces guardrails.
5. `TradeExecutor` simulates or submits orders; `DecisionLoop` stitches it all together.

## Setup
1. Install dependencies (editable mode): `python -m pip install -e .`
2. Copy config templates:
   - `cp config.example.json config.json` and fill in Hyperliquid keys/addresses.
   - `cp .env.example .env` and set LLM/news/risk toggles.
3. Optional sanity check for example data script: `PYTHONPATH=. python src/data/account_info.py`

## Running the loop
- Default (single iteration, dry-run): `PYTHONPATH=. RUN_ONCE=true python -m src.runner`
- Continuous loop: set `RUN_ONCE=false` in `.env` (or env) to poll every `POLL_INTERVAL_SECONDS`.
- Configure symbols/timeframes via `.env` (`SYMBOL`, `TIMEFRAMES`) and Hyperliquid credentials via `config.json`.

## Notes and next steps
- LLM and news integrations are placeholders; add real API calls where TODOs are marked.
- Risk controls are minimal; extend with position sizing, PnL tracking, and rate limits.
- Add tests near new functionality (`tests/`) and mock external calls.
- For a quick ETH market/indicator fetch using your `config.json`, run `PYTHONPATH=. python tests/market_data.py`.
- To check account balances/positions, run `PYTHONPATH=. python tests/account_info.py`.
- To see a demo prompt composed from live data, run `PYTHONPATH=. python tests/prompt_builder_demo.py`.
