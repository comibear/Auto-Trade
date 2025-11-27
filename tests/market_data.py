"""Smoke script to pull Hyperliquid market data for ETH and parse indicators.

Uses config.json in the repo root (src.utils.setup). Prints headline metrics,
intraday indicator samples (5m), and 4h summary indicators.

Usage:
    PYTHONPATH=. python tests/market_data.py
"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

try:
    from src.clients.hyperliquid_client import HyperliquidClient
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Missing dependency; install hyperliquid-python-sdk in your environment.\n"
        "Example: python -m pip install hyperliquid-python-sdk"
    ) from exc
from src.config.settings import HyperliquidSettings
from src.data.market_data_service import MarketDataService
from src.data.market_parser import parse_market


def _format_candle(candle) -> str:
    """Render a compact candle line."""
    return (
        f"ts={candle.timestamp_ms} "
        f"o={candle.open} h={candle.high} l={candle.low} c={candle.close} v={candle.volume}"
    )


def _print_candles(timeframe: str, candles: Iterable) -> None:
    """Print first/last candle for quick inspection."""
    candle_list = list(candles)
    if not candle_list:
        print(f"  [{timeframe}] no candles returned")
        return
    first = candle_list[0]
    last = candle_list[-1]
    print(f"  [{timeframe}] count={len(candle_list)}")
    print(f"    first: {_format_candle(first)}")
    print(f"    last : {_format_candle(last)}")


def fetch_eth_snapshot() -> None:
    """Fetch ETH snapshot and print headline metrics and indicators."""
    settings = HyperliquidSettings(
        symbol="ETH",
        timeframes=["5m", "4h"],
        skip_ws=True,
    )
    client = HyperliquidClient(
        base_url=settings.base_url,
        skip_ws=settings.skip_ws,
        perp_dexs=settings.perp_dexs,
    )
    # Lookback to cover intraday (24h) and multi-day for 4h EMAs
    lookback_ms = int(timedelta(days=10).total_seconds() * 1000)
    # Fetch extra candles for stable indicators; output will still show the latest 10.
    market_service = MarketDataService(client=client, default_lookback_ms=lookback_ms, candle_limit=50)

    snapshot = market_service.collect_snapshot(
        symbol=settings.symbol, timeframes=settings.timeframes, lookback_ms=lookback_ms
    )
    parsed = parse_market(snapshot)

    print(f"Symbol: {snapshot.symbol}")
    print(f"Collected at: {snapshot.collected_at}")
    print(f"Mark price: {snapshot.mark_price}")
    print(f"Open interest: latest={parsed.open_interest_latest}, avg={parsed.open_interest_average}")
    print(f"Funding rate: {parsed.funding_rate}")
    print("--- Intraday (5m) ---")
    if parsed.intraday_series:
        print(f"Current EMA20: {parsed.current_ema20}")
        print(f"Current MACD: {parsed.current_macd}")
        print(f"Current RSI7: {parsed.current_rsi7}")
        _print_candles(
            parsed.intraday_series.timeframe,
            snapshot.candles_by_timeframe.get("5m", []),
        )
    else:
        print("No intraday data available.")

    print("--- 4h Summary ---")
    if parsed.four_hour_summary:
        fh = parsed.four_hour_summary
        print(
            f"EMA20={fh.ema20}, EMA50={fh.ema50}, ATR3={fh.atr3}, ATR14={fh.atr14}, "
            f"Vol={fh.current_volume}, VolAvg={fh.average_volume}, MACD={fh.macd}, RSI14={fh.rsi14}"
        )
        _print_candles("4h", snapshot.candles_by_timeframe.get("4h", []))
    else:
        print("No 4h data available.")


if __name__ == "__main__":
    fetch_eth_snapshot()
