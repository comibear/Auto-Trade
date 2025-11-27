"""Build and print a demo prompt from live market + account data.

Uses `config.json` for Hyperliquid authentication (via src.utils.setup). Fetches:
- Market snapshot for BTC (5m intraday + 4h context)
- Account snapshot (balances, margin, positions)
- Parsed indicators (EMA, MACD, RSI, ATR)
Then renders a human-readable prompt similar to the example provided.

Usage:
    PYTHONPATH=. python tests/prompt_builder_demo.py
"""

from __future__ import annotations

from datetime import timedelta

try:
    from src.agent.prompt_builder import build_demo_prompt
    from src.clients.hyperliquid_client import HyperliquidClient
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Missing dependency; install hyperliquid-python-sdk in your environment.\n"
        "Example: python -m pip install hyperliquid-python-sdk"
    ) from exc

from src.config.settings import HyperliquidSettings
from src.data.account_service import AccountService
from src.data.market_data_service import MarketDataService
from src.data.market_parser import parse_market


def main() -> None:
    settings = HyperliquidSettings(symbol="BTC", timeframes=["5m", "4h"], skip_ws=True)
    client = HyperliquidClient(
        base_url=settings.base_url,
        skip_ws=settings.skip_ws,
        perp_dexs=settings.perp_dexs,
    )

    lookback_ms = int(timedelta(days=10).total_seconds() * 1000)
    # Fetch extra candles for stable indicators; output will still show the latest 10.
    market_service = MarketDataService(client=client, default_lookback_ms=lookback_ms, candle_limit=50)
    snapshot = market_service.collect_snapshot(
        symbol=settings.symbol, timeframes=settings.timeframes, lookback_ms=lookback_ms
    )
    parsed_market = parse_market(snapshot)

    account_service = AccountService(client)
    account_info = account_service.fetch_account_info()

    prompt = build_demo_prompt(parsed_market, account_info)
    
    with open("prompt.txt", "w") as f:
        f.write(prompt)
    print("Prompt saved to prompt.txt")


if __name__ == "__main__":
    main()
