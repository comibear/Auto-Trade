"""Shared data models for market and news payloads."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Candle:
    """Represents a single OHLCV candle."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketDataSnapshot:
    """Aggregated market data for a symbol across multiple timeframes."""

    symbol: str
    candles_by_timeframe: Dict[str, List[Candle]]
    open_interest: Optional[float]
    funding_rate: Optional[float]
    mark_price: Optional[float]
    metadata: Dict[str, Any]
    collected_at: datetime


@dataclass
class MACDPoint:
    """MACD-related values for a given observation."""

    macd: float
    signal: float
    histogram: float


@dataclass
class IntradaySeries:
    """Five-minute series metrics."""

    timeframe: str
    mid_prices: List[float]
    ema20: List[float]
    macd: List[MACDPoint]
    rsi7: List[float | None]
    rsi14: List[float | None]


@dataclass
class FourHourSummary:
    """4h timeframe metrics."""

    ema20: Optional[float]
    ema50: Optional[float]
    atr3: Optional[float]
    atr14: Optional[float]
    current_volume: Optional[float]
    average_volume: Optional[float]
    macd: Optional[MACDPoint]
    macd_series: List[MACDPoint] = field(default_factory=list)
    rsi14: Optional[float] = None
    rsi14_series: List[float | None] = field(default_factory=list)


@dataclass
class MarketParseResult:
    """Aggregated indicator snapshot across timeframes."""

    symbol: str
    current_price: Optional[float]
    current_ema20: Optional[float]
    current_macd: Optional[MACDPoint]
    current_rsi7: Optional[float]
    open_interest_latest: Optional[float]
    open_interest_average: Optional[float]
    funding_rate: Optional[float]
    intraday_series: Optional[IntradaySeries]
    four_hour_summary: Optional[FourHourSummary]


@dataclass
class Position:
    """Simplified view of an open position."""

    symbol: str
    size: float
    entry_price: float
    liquidation_price: Optional[float] = None
    leverage: Optional[float] = None
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountInfo:
    """Current account snapshot."""

    address: str
    account_value: Optional[float]
    total_margin_used: Optional[float]
    available_cash: Optional[float]
    margin_ratio: Optional[float]
    total_return_pct: Optional[float] = None
    positions: List[Position] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsHeadline:
    """Structured news headline for downstream prompt construction."""

    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
