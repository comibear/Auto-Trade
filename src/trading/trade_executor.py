"""Trade execution layer built on the Hyperliquid client."""

import logging
from typing import Dict

from src.agent.decision_schema import Action, LLMDecision
from src.clients.hyperliquid_client import HyperliquidClient
from src.config.settings import RiskSettings
from src.trading.risk_management import RiskManager

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Executes trades after applying risk checks."""

    def __init__(self, client: HyperliquidClient, risk_manager: RiskManager, risk_settings: RiskSettings):
        self.client = client
        self.risk_manager = risk_manager
        self.risk_settings = risk_settings

    def execute(self, decision: LLMDecision, symbol: str) -> Dict[str, object]:
        """Execute or simulate the trade based on the decision."""
        decision = self.risk_manager.enforce(decision)
        if decision.action == Action.NO_TRADE:
            logger.info("No trade executed for %s. Reason: %s", symbol, decision.reasoning)
            return {"status": "skipped", "reason": decision.reasoning}

        logger.info(
            "Executing trade: %s %s leverage=%s tp=%s sl=%s",
            decision.action,
            symbol,
            decision.leverage,
            decision.take_profit,
            decision.stop_loss,
        )

        if self.risk_settings.dry_run:
            logger.info("Dry-run mode enabled; simulating order submission.")
            return {
                "status": "simulated",
                "symbol": symbol,
                "action": decision.action.value,
                "leverage": decision.leverage,
                "take_profit": decision.take_profit,
                "stop_loss": decision.stop_loss,
            }

        side = "buy" if decision.action == Action.LONG else "sell"
        # TODO: derive position size from strategy/risk preferences.
        size = 1.0
        response = self.client.place_order(
            symbol=symbol,
            side=side,
            size=size,
            leverage=decision.leverage,
            take_profit=decision.take_profit,
            stop_loss=decision.stop_loss,
        )
        logger.info("Order response: %s", response)
        return response
