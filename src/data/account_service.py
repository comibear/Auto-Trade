"""Account information fetcher built on the Hyperliquid client."""

from __future__ import annotations

import logging
from typing import Dict, List

from src.clients.hyperliquid_client import HyperliquidClient
from src.data.models import AccountInfo, Position

logger = logging.getLogger(__name__)


class AccountService:
    """Fetch account balances, margin, and open positions."""

    def __init__(self, client: HyperliquidClient):
        self.client = client

    def fetch_account_info(self) -> AccountInfo:
        """Retrieve account state and normalize into AccountInfo."""
        user_state = self.client.info.user_state(self.client.address)
        margin_summary: Dict[str, object] = user_state.get("marginSummary", {})
        positions: List[Position] = []

        for asset in user_state.get("assetPositions", []):
            asset_symbol = _resolve_symbol(asset)
            pos = asset.get("position", {})
            size = float(pos.get("szi", 0.0))
            if size == 0:
                continue
            positions.append(
                Position(
                    symbol=asset_symbol,
                    size=size,
                    entry_price=float(pos.get("entryPx", 0.0)),
                    liquidation_price=float(pos.get("liquidationPx", 0.0))
                    if pos.get("liquidationPx") is not None
                    else None,
                    leverage=_to_float(pos.get("leverage")),
                    current_price=float(pos.get("markPx", 0.0)) if pos.get("markPx") else None,
                    unrealized_pnl=float(pos.get("unrealizedPnl", 0.0))
                    if pos.get("unrealizedPnl") is not None
                    else None,
                    extra={"asset": asset_symbol, **pos},
                )
            )

        account_value = _to_float(margin_summary.get("accountValue"))
        total_margin_used = _to_float(margin_summary.get("totalMarginUsed"))
        available_cash = (
            account_value - total_margin_used
            if account_value is not None and total_margin_used is not None
            else None
        )
        margin_ratio = _to_float(margin_summary.get("marginRatio"))

        logger.info(
            "Fetched account info: value=%s, margin_used=%s, positions=%s",
            account_value,
            total_margin_used,
            len(positions),
        )

        return AccountInfo(
            address=self.client.address,
            account_value=account_value,
            total_margin_used=total_margin_used,
            available_cash=available_cash,
            margin_ratio=margin_ratio,
            total_return_pct=None,
            positions=positions,
            raw=user_state,
        )


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, dict):
        # Attempt to unwrap common dict formats, e.g., {"value": x}
        for key in ("value", "val", "amount"):
            if key in value:
                return _to_float(value[key])
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_symbol(asset: Dict[str, object]) -> str:
    """
    Try to derive the symbol from various possible shapes:
    - asset["asset"] as string/dict/int
    - asset["coin"] / asset["symbol"]
    - If dict, prefer ["name"] or ["symbol"] fields.
    """
    candidate = asset.get("asset")
    if isinstance(candidate, dict):
        for key in ("name", "symbol", "coin"):
            if key in candidate and candidate[key]:
                return str(candidate[key])
    if candidate:
        return str(candidate)
    for key in ("coin", "symbol", "name"):
        val = asset.get(key)
        if val:
            return str(val)
    return ""
