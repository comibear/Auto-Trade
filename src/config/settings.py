"""Configuration helpers for the automated trading system."""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


def _split_csv(value: str, default: List[str]) -> List[str]:
    """Split a comma-separated string into a list with fallback to default."""
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class HyperliquidSettings:
    """Hyperliquid-specific configuration."""

    base_url: Optional[str] = None
    symbol: str = "BTC"
    timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "1h"])
    skip_ws: bool = True
    perp_dexs: Optional[str] = None
    config_path: str = "config.json"


@dataclass
class LLMSettings:
    """Settings for the LLM provider."""

    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 512


@dataclass
class NewsSettings:
    """News provider configuration (future extension)."""

    enabled: bool = False
    provider: Optional[str] = None
    api_key: Optional[str] = None
    max_headlines: int = 10


@dataclass
class RiskSettings:
    """Simple risk guardrails."""

    max_leverage: float = 5.0
    max_position_notional: float = 1000.0
    max_daily_loss: float = 500.0
    dry_run: bool = True


@dataclass
class AppSettings:
    """Aggregate settings used across the pipeline."""

    poll_interval_seconds: int = 60
    hyperliquid: HyperliquidSettings = field(default_factory=HyperliquidSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    news: NewsSettings = field(default_factory=NewsSettings)
    risk: RiskSettings = field(default_factory=RiskSettings)

    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        Load settings from environment variables with sensible defaults.

        Hyperliquid keys are still expected to live in ``config.json`` and are
        consumed by ``src.utils.setup``.
        """
        hyperliquid_defaults = HyperliquidSettings()
        hyperliquid = HyperliquidSettings(
            base_url=os.getenv("HL_BASE_URL"),
            symbol=os.getenv("SYMBOL", hyperliquid_defaults.symbol),
            timeframes=_split_csv(
                os.getenv("TIMEFRAMES", ""), hyperliquid_defaults.timeframes
            ),
            skip_ws=os.getenv("HL_SKIP_WS", "true").lower() == "true",
            perp_dexs=os.getenv("HL_PERP_DEXS"),
            config_path=os.getenv("HL_CONFIG_PATH", hyperliquid_defaults.config_path),
        )
        llm = LLMSettings(
            provider=os.getenv("LLM_PROVIDER", LLMSettings.provider),
            model=os.getenv("LLM_MODEL", LLMSettings.model),
            api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", LLMSettings.temperature)),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", LLMSettings.max_tokens)),
        )
        news = NewsSettings(
            enabled=os.getenv("NEWS_ENABLED", "false").lower() == "true",
            provider=os.getenv("NEWS_PROVIDER"),
            api_key=os.getenv("NEWS_API_KEY"),
            max_headlines=int(os.getenv("NEWS_MAX_HEADLINES", NewsSettings.max_headlines)),
        )
        risk = RiskSettings(
            max_leverage=float(os.getenv("MAX_LEVERAGE", RiskSettings.max_leverage)),
            max_position_notional=float(
                os.getenv("MAX_POSITION_NOTIONAL", RiskSettings.max_position_notional)
            ),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", RiskSettings.max_daily_loss)),
            dry_run=os.getenv("DRY_RUN", "true").lower() == "true",
        )
        return cls(
            poll_interval_seconds=int(
                os.getenv("POLL_INTERVAL_SECONDS", AppSettings.poll_interval_seconds)
            ),
            hyperliquid=hyperliquid,
            llm=llm,
            news=news,
            risk=risk,
        )

    @classmethod
    def from_json(cls, path: str) -> "AppSettings":
        """Load settings from a JSON file; useful for deployments or tests."""
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(
            poll_interval_seconds=payload.get(
                "poll_interval_seconds", AppSettings.poll_interval_seconds
            ),
            hyperliquid=HyperliquidSettings(**payload.get("hyperliquid", {})),
            llm=LLMSettings(**payload.get("llm", {})),
            news=NewsSettings(**payload.get("news", {})),
            risk=RiskSettings(**payload.get("risk", {})),
        )
