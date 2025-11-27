"""Build a trading prompt and send it to the LLM using environment config.

Requires:
- Hyperliquid credentials in config.json (used by src.utils.setup)
- OPENAI_API_KEY (or LLM_API_KEY) in environment/.env
- openai package installed (`python -m pip install openai`)
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional

from src.agent.prompt_builder import build_demo_prompt
from src.clients.hyperliquid_client import HyperliquidClient
from src.config.settings import HyperliquidSettings
from src.data.account_service import AccountService
from src.data.market_data_service import MarketDataService
from src.data.market_parser import parse_market

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: install openai\n"
        "Example: python -m pip install openai"
    ) from exc

from dotenv import load_dotenv
load_dotenv()

def run_prompt(model: str, api_key: str, symbol: str = "BTC") -> str:
    """Fetch market/account state, build prompt, send to LLM, and return reply."""
    settings = HyperliquidSettings(symbol=symbol, timeframes=["5m", "4h"], skip_ws=True)
    client = HyperliquidClient(
        base_url=settings.base_url,
        skip_ws=settings.skip_ws,
        perp_dexs=settings.perp_dexs,
    )

    lookback_ms = int(timedelta(days=10).total_seconds() * 1000)
    market_service = MarketDataService(client=client, default_lookback_ms=lookback_ms, candle_limit=50)
    market_snapshot = market_service.collect_snapshot(
        symbol=settings.symbol, timeframes=settings.timeframes, lookback_ms=lookback_ms
    )
    parsed_market = parse_market(market_snapshot)

    account_service = AccountService(client)
    account_info = account_service.fetch_account_info()

    prompt = build_demo_prompt(parsed_market, account_info)
    print("==== Prompt ====")
    print(prompt)
    print("================")

    openai_client = OpenAI(api_key=api_key)
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content
    return reply


def main() -> None:
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not found in environment/.env")
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    symbol = os.getenv("SYMBOL", "BTC")

    reply = run_prompt(model=model, api_key=api_key, symbol=symbol)
    print("==== LLM Reply ====")
    print(reply)


if __name__ == "__main__":
    main()
