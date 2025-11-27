"""Market data parser and indicator calculator."""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Sequence, Tuple

from src.data.models import (
    Candle,
    FourHourSummary,
    IntradaySeries,
    MACDPoint,
    MarketDataSnapshot,
    MarketParseResult,
)

logger = logging.getLogger(__name__)


# ----- Indicator utilities ----------------------------------------------------

def ema(values: Sequence[float], period: int) -> List[float]:
    """Compute exponential moving average."""
    if not values:
        return []
    if period <= 0:
        raise ValueError("period must be positive")
    alpha = 2 / (period + 1)
    ema_values: List[float] = []
    ema_prev: float | None = None
    for value in values:
        if ema_prev is None:
            ema_prev = value
        else:
            ema_prev = (value - ema_prev) * alpha + ema_prev
        ema_values.append(ema_prev)
    return ema_values


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> List[MACDPoint]:
    """Compute MACD line, signal, and histogram."""
    if not values:
        return []
    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    # Align lengths (pad shorter with leading None-like)
    macd_line: List[float] = []
    for f, s in zip(fast_ema, slow_ema):
        macd_line.append(f - s)
    signal_line = ema(macd_line, signal)
    macd_points: List[MACDPoint] = []
    for m, s in zip(macd_line, signal_line):
        macd_points.append(MACDPoint(macd=m, signal=s, histogram=m - s))
    return macd_points


def rsi(values: Sequence[float], period: int) -> List[float | None]:
    """Compute RSI using Wilder's smoothing over ``period`` candles (not days)."""
    if not values:
        return []
    if period <= 0:
        raise ValueError("period must be positive")
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [abs(min(delta, 0.0)) for delta in deltas]

    if len(values) < period + 1:
        return [None] * len(values)

    rsi_values: List[float | None] = [None] * len(values)

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # First RSI value corresponds to index `period`
    rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
    rsi_values[period] = 100 - (100 / (1 + rs))

    for i in range(period + 1, len(values)):
        gain = gains[i - 1]  # offset by one because gains length is len(values)-1
        loss = losses[i - 1]
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
        rsi_values[i] = 100 - (100 / (1 + rs))

    return rsi_values


def atr(candles: Sequence[Candle], period: int) -> List[float]:
    """Compute Average True Range using Wilder's smoothing."""
    if not candles:
        return []
    trs: List[float] = []
    prev_close: Optional[float] = None
    for candle in candles:
        high, low, close = candle.high, candle.low, candle.close
        if prev_close is None:
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
        trs.append(tr)
        prev_close = close

    if len(trs) < period:
        return []

    atr_values: List[float] = []
    # initial ATR: simple average of first period TRs
    atr_prev = sum(trs[:period]) / period
    atr_values.extend([0.0] * (period - 1))
    atr_values.append(atr_prev)

    for tr in trs[period:]:
        atr_prev = ((atr_prev * (period - 1)) + tr) / period
        atr_values.append(atr_prev)
    return atr_values


def moving_average(values: Sequence[float]) -> Optional[float]:
    """Simple average helper."""
    if not values:
        return None
    return sum(values) / len(values)


# ----- Parsing helpers --------------------------------------------------------

def _ensure_sorted(candles: Iterable[Candle]) -> List[Candle]:
    """Ensure candles are sorted by timestamp ascending."""
    return sorted(candles, key=lambda c: c.timestamp_ms)


def _extract_close_series(candles: Sequence[Candle]) -> List[float]:
    return [c.close for c in candles]


def _extract_mid_prices(candles: Sequence[Candle]) -> List[float]:
    return [(c.high + c.low) / 2 for c in candles]


def _latest(values: Sequence[float]) -> Optional[float]:
    return values[-1] if values else None


def _latest_non_none(values: Sequence[float | None]) -> Optional[float]:
    for value in reversed(values):
        if value is not None:
            return value
    return None


def _compact(values: Sequence[float | None]) -> List[float]:
    """Remove None values, preserving order."""
    return [v for v in values if v is not None]


def parse_market(snapshot: MarketDataSnapshot) -> MarketParseResult:
    """
    Parse a MarketDataSnapshot into structured indicators.

    Assumptions:
    - Intraday metrics use 5m candles.
    - Current EMA/MACD/RSI use the 5m series.
    - 4h metrics use 4h candles.
    """
    five_min_candles = _ensure_sorted(snapshot.candles_by_timeframe.get("5m", []))
    four_hour_candles = _ensure_sorted(snapshot.candles_by_timeframe.get("4h", []))

    # ----- Intraday (5m) -----
    intraday_series: Optional[IntradaySeries] = None
    current_ema20 = current_macd = current_rsi7 = None
    if five_min_candles:
        closes_5m = _extract_close_series(five_min_candles)
        mids_5m = _extract_mid_prices(five_min_candles)
        ema20_series = ema(closes_5m, period=20)
        macd_series = macd(closes_5m)
        rsi7_series = _compact(rsi(closes_5m, period=7))
        rsi14_series = _compact(rsi(closes_5m, period=14))

        current_ema20 = _latest(ema20_series)
        current_macd = macd_series[-1] if macd_series else None
        current_rsi7 = _latest_non_none(rsi7_series)

        intraday_series = IntradaySeries(
            timeframe="5m",
            mid_prices=mids_5m,
            ema20=ema20_series,
            macd=macd_series,
            rsi7=rsi7_series,
            rsi14=rsi14_series,
        )
    else:
        logger.warning("No 5m candles available; intraday metrics will be empty.")

    # ----- 4h metrics -----
    four_hour_summary: Optional[FourHourSummary] = None
    if four_hour_candles:
        closes_4h = _extract_close_series(four_hour_candles)
        vols_4h = [c.volume for c in four_hour_candles]
        ema20_4h = ema(closes_4h, period=20)
        ema50_4h = ema(closes_4h, period=50)
        atr3_series = atr(four_hour_candles, period=3)
        atr14_series = atr(four_hour_candles, period=14)
        macd_4h = macd(closes_4h)
        rsi14_4h = rsi(closes_4h, period=14)

        four_hour_summary = FourHourSummary(
            ema20=_latest(ema20_4h),
            ema50=_latest(ema50_4h),
            atr3=_latest(atr3_series),
            atr14=_latest(atr14_series),
            current_volume=_latest(vols_4h),
            average_volume=moving_average(vols_4h),
            macd=macd_4h[-1] if macd_4h else None,
            macd_series=macd_4h,
            rsi14=_latest_non_none(rsi14_4h),
            rsi14_series=_compact(rsi14_4h),
        )
    else:
        logger.warning("No 4h candles available; 4h metrics will be empty.")

    # ----- Open interest -----
    oi_latest = snapshot.open_interest
    oi_average = oi_latest  # TODO: derive historical average when available.

    return MarketParseResult(
        symbol=snapshot.symbol,
        current_price=snapshot.mark_price,
        current_ema20=current_ema20,
        current_macd=current_macd,
        current_rsi7=current_rsi7,
        open_interest_latest=oi_latest,
        open_interest_average=oi_average,
        funding_rate=snapshot.funding_rate,
        intraday_series=intraday_series,
        four_hour_summary=four_hour_summary,
    )
