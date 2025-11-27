"""Service for gathering market data across multiple timeframes."""

import logging
from typing import List

from src.clients.hyperliquid_client import HyperliquidClient
from src.data.models import MarketDataSnapshot

logger = logging.getLogger(__name__)

class MarketDataService:
    """Coordinates candle and metric retrieval for a given trading symbol."""

    def __init__(
        self,
        client: HyperliquidClient,
        default_lookback_ms: int = 6 * 60 * 60 * 1000,
        candle_limit: int | None = None,
    ):
        self.client = client
        self.default_lookback_ms = default_lookback_ms
        self.candle_limit = candle_limit

    def collect_snapshot(
        self, symbol: str, timeframes: List[str], lookback_ms: int | None = None
    ) -> MarketDataSnapshot:
        """
        Collect candles, funding, and open interest for a symbol.

        The resulting snapshot is structured for prompt construction.
        """
        lookback = lookback_ms or self.default_lookback_ms
        logger.info(
            "Collecting market data for %s (timeframes=%s, lookback_ms=%s)",
            symbol,
            timeframes,
            lookback,
        )
        return self.client.fetch_market_snapshot(
            symbol=symbol,
            intervals=timeframes,
            lookback_ms=lookback,
            candle_limit=self.candle_limit,
        )
