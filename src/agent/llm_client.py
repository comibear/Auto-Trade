"""LLM client abstraction."""

import json
import logging
from typing import Dict, Optional

from src.agent.decision_schema import Action, LLMDecision

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around an LLM provider (e.g., OpenAI)."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        self.provider = provider
        self.api_key = api_key
        self.model = model

    def get_decision(self, prompt: str) -> LLMDecision:
        """
        Submit the prompt and parse the decision payload.

        TODO: integrate with the chosen LLM SDK once API keys are available.
        """
        logger.info("Sending prompt to LLM provider=%s model=%s", self.provider, self.model)
        if not self.api_key:
            logger.warning("No LLM API key configured; returning NO_TRADE decision.")
            return LLMDecision(
                action=Action.NO_TRADE,
                leverage=1.0,
                take_profit=None,
                stop_loss=None,
                confidence=None,
                reasoning="LLM disabled; defaulting to no-trade.",
            )

        # TODO: Replace this placeholder with a real client call.
        logger.debug("Prompt payload: %s", prompt)
        dummy_response = {
            "action": Action.NO_TRADE.value,
            "leverage": 1.0,
            "take_profit": None,
            "stop_loss": None,
            "confidence": 0.0,
            "reasoning": "Placeholder response until LLM integration is wired.",
        }
        logger.info("Received dummy decision from LLM client.")
        return LLMDecision.from_dict(dummy_response)

    @staticmethod
    def parse_response(raw_response: str | Dict[str, object]) -> LLMDecision:
        """Parse a raw LLM string/dict response into an ``LLMDecision`` instance."""
        if isinstance(raw_response, str):
            data = json.loads(raw_response)
        else:
            data = raw_response
        return LLMDecision.from_dict(data)
