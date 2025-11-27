"""Basic risk guardrails for automated execution."""

import logging
from typing import Tuple

from src.config.settings import RiskSettings
from src.agent.decision_schema import Action, LLMDecision

logger = logging.getLogger(__name__)


class RiskManager:
    """Applies static risk checks to LLM decisions."""

    def __init__(self, settings: RiskSettings):
        self.settings = settings

    def evaluate(self, decision: LLMDecision) -> Tuple[bool, str]:
        """Return a tuple indicating if the decision passes risk checks."""
        if decision.action == Action.NO_TRADE:
            return True, "No trade requested."

        if decision.leverage > self.settings.max_leverage:
            return False, f"Leverage {decision.leverage} exceeds max {self.settings.max_leverage}"

        # Placeholder for additional checks (daily loss, exposure caps, etc.).
        return True, "Decision passed risk filters."

    def enforce(self, decision: LLMDecision) -> LLMDecision:
        """
        Optionally adjust a decision to fit within risk limits.

        Currently returns the decision unchanged when limits are respected.
        """
        is_allowed, reason = self.evaluate(decision)
        if not is_allowed:
            logger.warning("Blocking decision due to risk policy: %s", reason)
            return LLMDecision(
                action=Action.NO_TRADE,
                leverage=1.0,
                take_profit=None,
                stop_loss=None,
                confidence=decision.confidence,
                reasoning=f"Blocked by risk management: {reason}",
                raw=decision.raw,
            )
        return decision
