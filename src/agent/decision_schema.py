"""Data structures representing LLM-driven trade decisions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class Action(str, Enum):
    """Supported trading actions."""

    LONG = "LONG"
    SHORT = "SHORT"
    NO_TRADE = "NO_TRADE"


@dataclass
class LLMDecision:
    """Structured response expected from the LLM."""

    action: Action
    leverage: float
    take_profit: Optional[float]
    stop_loss: Optional[float]
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "LLMDecision":
        """Build an ``LLMDecision`` from a dictionary."""
        return cls(
            action=Action(payload.get("action", Action.NO_TRADE)),
            leverage=float(payload.get("leverage", 1.0)),
            take_profit=payload.get("take_profit"),
            stop_loss=payload.get("stop_loss"),
            confidence=payload.get("confidence"),
            reasoning=payload.get("reasoning"),
            raw=payload,
        )
