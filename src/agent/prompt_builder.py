"""Prompt construction utilities for the trading decision agent."""

import json
from typing import Dict, List

from src.data.models import (
    AccountInfo,
    MACDPoint,
    MarketDataSnapshot,
    MarketParseResult,
    NewsHeadline,
    Position,
)

PROMPT_INSTRUCTIONS = (
    "You are a trading decision agent operating on Hyperliquid perpetuals. "
    "Given market metrics and optional news, decide to LONG, SHORT, or NO_TRADE. "
    "Always return JSON with keys: action, leverage, take_profit, stop_loss, confidence, reasoning."
)


def build_prompt_payload(
    market_data: MarketDataSnapshot, news: List[NewsHeadline]
) -> Dict[str, object]:
    """Prepare a structured payload to feed into an LLM."""
    candles = {}
    for tf, tf_candles in market_data.candles_by_timeframe.items():
        candles[tf] = [
            {
                "timestamp_ms": candle.timestamp_ms,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            }
            for candle in tf_candles
        ]

    return {
        "instructions": PROMPT_INSTRUCTIONS,
        "symbol": market_data.symbol,
        "mark_price": market_data.mark_price,
        "open_interest": market_data.open_interest,
        "funding_rate": market_data.funding_rate,
        "candles": candles,
        "news": [
            {
                "title": item.title,
                "source": item.source,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "summary": item.summary,
                "tags": item.tags,
                "url": item.url,
            }
            for item in news
        ],
    }


def build_prompt_text(payload: Dict[str, object]) -> str:
    """Render the payload into a compact text prompt."""
    return (
        f"{payload['instructions']}\n\n"
        f"Symbol: {payload['symbol']}\n"
        f"Mark price: {payload.get('mark_price')}\n"
        f"Open interest: {payload.get('open_interest')}\n"
        f"Funding rate: {payload.get('funding_rate')}\n"
        f"Candles: {json.dumps(payload.get('candles'), default=str)}\n"
        f"News: {json.dumps(payload.get('news'), default=str)}\n"
        "Respond with JSON only."
    )


def build_demo_prompt(market: MarketParseResult, account: AccountInfo) -> str:
    """
    Build a human-readable, structured prompt combining market indicators and account info.
    Output is plain text with clearly labeled sections (not JSON) to guide the LLM.
    """

    def _fmt_positions(positions: List[Position]) -> str:
        if not positions:
            return "  - None"
        lines = []
        for pos in positions:
            sym = pos.symbol or pos.extra.get("asset") or pos.extra.get("symbol") or pos.extra.get("coin")
            lines.append(
                f"  - {sym}: qty={pos.size}, entry={pos.entry_price}, "
                f"px={pos.current_price}, liq={pos.liquidation_price}, "
                f"unrealized_pnl={pos.unrealized_pnl}, lev={pos.leverage}"
            )
        return "\n".join(lines)

    def _fmt_macd_series(series: List[MACDPoint]) -> str:
        return "[" + ", ".join(f"{m.macd:.3f}" for m in series) + "]" if series else "[]"

    def _fmt_macd_point(point: MACDPoint | None) -> str:
        if point is None:
            return "None"
        return f"macd={point.macd}, signal={point.signal}, hist={point.histogram}"

    def _fmt_macd_series(series: List[MACDPoint]) -> str:
        return "[" + ", ".join(f"{m.macd:.3f}" for m in series) + "]" if series else "[]"

    def _fmt_rsi(series: List[float | None]) -> str:
        clean = [v for v in series if v is not None]
        return "[" + ", ".join(f"{v:.3f}" for v in clean) + "]" if clean else "[]"

    intraday_section = ""
    if market.intraday_series:
        intraday = market.intraday_series
        # Display only the latest 10 entries for readability.
        mids = intraday.mid_prices[-10:]
        ema20 = intraday.ema20[-10:]
        macd_tail = intraday.macd[-10:]
        rsi7_tail = intraday.rsi7[-10:]
        rsi14_tail = intraday.rsi14[-10:]
        intraday_section = (
            "Intraday (5m, oldest→latest):\n"
            f"- Mid prices: {mids}\n"
            f"- EMA20: {ema20}\n"
            f"- MACD line: {_fmt_macd_series(macd_tail)}\n"
            f"- RSI7: {_fmt_rsi(rsi7_tail)}\n"
            f"- RSI14: {_fmt_rsi(rsi14_tail)}\n"
        )

    four_h_section = ""
    if market.four_hour_summary:
        fh = market.four_hour_summary
        macd_tail = fh.macd_series[-10:] if fh.macd_series else []
        rsi14_tail = fh.rsi14_series[-10:] if fh.rsi14_series else []
        four_h_section = (
            "4h timeframe:\n"
            f"- EMA20 vs EMA50: {fh.ema20} vs {fh.ema50}\n"
            f"- ATR3 vs ATR14: {fh.atr3} vs {fh.atr14}\n"
            f"- Volume current vs average: {fh.current_volume} vs {fh.average_volume}\n"
            f"- MACD latest: {_fmt_macd_point(fh.macd)}\n"
            f"- MACD series (oldest→latest): {_fmt_macd_series(macd_tail)}\n"
            f"- RSI14 latest: {fh.rsi14}\n"
            f"- RSI14 series (oldest→latest): {_fmt_rsi(rsi14_tail)}\n"
        )

    account_section = (
        "Account info:\n"
        f"- Address: {account.address}\n"
        f"- Account value: {account.account_value}\n"
        f"- Available cash: {account.available_cash}\n"
        f"- Margin ratio: {account.margin_ratio}\n"
        f"- Total return (%): {account.total_return_pct}\n"
        f"- Positions:\n{_fmt_positions(account.positions)}\n"
    )

    return (
        "INSTRUCTIONS: You are a trading decision agent on Hyperliquid perps. "
        "Decide LONG, SHORT, or NO_TRADE with leverage, TP, SL. "
        "Respond ONLY with JSON keys: action, leverage, take_profit, stop_loss, confidence, reasoning.\n\n"
        "MARKET STATE:\n"
        f"- Symbol: {market.symbol}\n"
        f"- Current price: {market.current_price}\n"
        f"- Current EMA20: {market.current_ema20}\n"
        f"- Current MACD: {_fmt_macd_point(market.current_macd)}\n"
        f"- Current RSI7: {market.current_rsi7}\n"
        f"- Open interest (latest/avg): {market.open_interest_latest} / {market.open_interest_average}\n"
        f"- Funding rate: {market.funding_rate}\n"
        f"{intraday_section}\n"
        f"{four_h_section}\n"
        f"{account_section}"
    )


def _macd_dict(point: MACDPoint | None) -> Dict[str, float] | None:
    if point is None:
        return None
    return {"macd": point.macd, "signal": point.signal, "histogram": point.histogram}


def _json_default(obj):
    if isinstance(obj, MACDPoint):
        return _macd_dict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)
