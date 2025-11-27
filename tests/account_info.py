"""Fetch and print current Hyperliquid account information.

Uses config.json in the repo root (via src.utils.setup). Prints account value,
margin usage, available cash, and open positions.

Usage:
    PYTHONPATH=. python tests/account_info.py
"""

from __future__ import annotations

try:
    from src.clients.hyperliquid_client import HyperliquidClient
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Missing dependency; install hyperliquid-python-sdk in your environment.\n"
        "Example: python -m pip install hyperliquid-python-sdk"
    ) from exc
from src.data.account_service import AccountService


def main() -> None:
    client = HyperliquidClient()
    service = AccountService(client)
    info = service.fetch_account_info()

    print(f"Address: {info.address}")
    print(f"Account value: {info.account_value}")
    print(f"Total margin used: {info.total_margin_used}")
    print(f"Available cash (approx): {info.available_cash}")
    print(f"Margin ratio: {info.margin_ratio}")
    if info.positions:
        print("Open positions:")
        for pos in info.positions:
            print(
                f"  - {pos.symbol}: size={pos.size}, entry={pos.entry_price}, "
                f"liq={pos.liquidation_price}, lev={pos.leverage}"
            )
    else:
        print("No open positions.")


if __name__ == "__main__":
    main()
