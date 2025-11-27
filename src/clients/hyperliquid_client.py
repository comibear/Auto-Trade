"""Lightweight wrapper around the Hyperliquid SDK."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from hyperliquid.utils import constants

from src.data.models import Candle, MarketDataSnapshot
from src.utils import setup

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """
    Convenience client that centralizes Hyperliquid interactions.

    The low-level authentication and wiring still relies on ``src.utils.setup``
    to avoid duplicating SDK bootstrap logic.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        skip_ws: bool = True,
        perp_dexs: Optional[str] = None,
    ) -> None:
        self.address, self.info, self.exchange = setup(
            base_url=base_url or constants.MAINNET_API_URL,
            skip_ws=skip_ws,
            perp_dexs=perp_dexs,
        )
        logger.info("Hyperliquid client initialized for address %s", self.address)

    def fetch_candles(
        self, symbol: str, interval: str, start_ms: int, end_ms: int, limit: int | None = None
    ) -> List[Candle]:
        """
        Fetch candle snapshots for a symbol and interval.

        TODO: add paging if the API limits response size.
        """
        raw_candles = self.info.candles_snapshot(symbol, interval, start_ms, end_ms)
        candles: List[Candle] = []
        for entry in raw_candles:
            try:
                candles.append(self._to_candle(entry))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed candle entry %s: %s", entry, exc)
        if limit is not None:
            candles = candles[-limit:]
        return candles

    def fetch_market_metadata(self) -> Dict[str, Any]:
        """Fetch market metadata; this can feed open interest and funding lookups."""
        meta, asset_contexts = self.info.meta_and_asset_ctxs()
        return {"meta": meta, "asset_contexts": asset_contexts}

    def fetch_market_snapshot(
        self, symbol: str, intervals: List[str], lookback_ms: int, candle_limit: int | None = None
    ) -> MarketDataSnapshot:
        """
        Collect a multi-timeframe snapshot for a symbol.

        This call is intended for prompt building and quick strategy evaluation.
        """
        now_ms = int(time.time() * 1000)
        candles_by_timeframe = {}
        for interval in intervals:
            candles_by_timeframe[interval] = self.fetch_candles(
                symbol=symbol,
                interval=interval,
                start_ms=now_ms - lookback_ms,
                end_ms=now_ms,
                limit=candle_limit,
            )

        metadata = self.fetch_market_metadata()
        open_interest, funding_rate, mark_price = self._extract_asset_metrics(
            symbol, metadata
        )

        return MarketDataSnapshot(
            symbol=symbol,
            candles_by_timeframe=candles_by_timeframe,
            open_interest=open_interest,
            funding_rate=funding_rate,
            mark_price=mark_price,
            metadata=metadata,
            collected_at=datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc),
        )

    def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        leverage: float,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Submit an order through the Hyperliquid exchange client.

        TODO: translate into the precise SDK order payload once strategy rules are defined.
        """
        logger.info(
            "Placing order %s %s size=%s lev=%s tp=%s sl=%s",
            side,
            symbol,
            size,
            leverage,
            take_profit,
            stop_loss,
        )
        if self.exchange is None:
            raise RuntimeError("Exchange client is not initialized")

        # TODO: map to Hyperliquid order structure; for now we only log the intent.
        return {
            "symbol": symbol,
            "side": side,
            "size": size,
            "leverage": leverage,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "status": "simulated",
        }

    @staticmethod
    def _to_candle(raw: Any) -> Candle:
        """
        Convert a raw Hyperliquid candle payload to a ``Candle`` dataclass.

        Supports both list/tuple form: [timestamp_ms, open, close, high, low, volume, ...]
        and dict form with common keys (t/time, o/open, c/close, h/high, l/low, v/volume).
        """

        def _get(mapping: Dict[str, Any], *keys: str) -> Any:
            for key in keys:
                if key in mapping:
                    return mapping[key]
            raise KeyError(keys)

        if isinstance(raw, dict):
            ts = _get(raw, "t", "time", "timestamp", "timestamp_ms")
            o = _get(raw, "o", "open")
            c = _get(raw, "c", "close")
            h = _get(raw, "h", "high")
            l = _get(raw, "l", "low")
            v = _get(raw, "v", "volume")
        else:
            ts, o, c, h, l, v = raw[0], raw[1], raw[2], raw[3], raw[4], raw[5]

        return Candle(
            timestamp_ms=int(ts),
            open=float(o),
            close=float(c),
            high=float(h),
            low=float(l),
            volume=float(v),
            extra={"raw": raw},
        )

    @staticmethod
    def _extract_asset_metrics(symbol: str, metadata: Dict[str, Any]) -> Any:
        """Attempt to pull open interest, funding, and mark price from metadata."""
        meta = metadata.get("meta", {})
        asset_contexts = metadata.get("asset_contexts", [])
        for asset_meta, ctx in zip(meta.get("universe", []), asset_contexts):
            if asset_meta.get("name") == symbol:
                return (
                    float(ctx.get("openInterest", 0.0)),
                    float(ctx.get("funding", 0.0)),
                    float(ctx.get("markPx", 0.0)),
                )
        logger.warning("Symbol %s not found in metadata; skipping metrics extraction", symbol)
        return None, None, None
