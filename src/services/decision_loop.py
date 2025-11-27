"""Orchestrates the fetch → decide → execute loop."""

import logging
import time
from typing import Dict, Optional

from src.agent.llm_client import LLMClient
from src.agent.prompt_builder import build_prompt_payload, build_prompt_text
from src.config.settings import AppSettings
from src.data.market_data_service import MarketDataService
from src.data.news_service import NewsService
from src.trading.trade_executor import TradeExecutor

logger = logging.getLogger(__name__)


class DecisionLoop:
    """Main control loop for the automated trading system."""

    def __init__(
        self,
        settings: AppSettings,
        market_data: MarketDataService,
        llm_client: LLMClient,
        executor: TradeExecutor,
        news_service: Optional[NewsService] = None,
    ):
        self.settings = settings
        self.market_data = market_data
        self.news_service = news_service
        self.llm_client = llm_client
        self.executor = executor

    def run_once(self) -> Dict[str, object]:
        """Execute one full iteration of the pipeline."""
        symbol = self.settings.hyperliquid.symbol
        market_snapshot = self.market_data.collect_snapshot(
            symbol=symbol, timeframes=self.settings.hyperliquid.timeframes
        )

        news = []
        if self.settings.news.enabled and self.news_service:
            news = self.news_service.fetch(self.settings.news.max_headlines)

        payload = build_prompt_payload(market_snapshot, news)
        prompt = build_prompt_text(payload)
        decision = self.llm_client.get_decision(prompt)
        execution = self.executor.execute(decision, symbol)
        result = {"decision": decision, "execution": execution}
        logger.info("Decision loop result: %s", execution)
        return result

    def run_forever(self) -> None:
        """
        Keep running the loop on the configured interval.

        TODO: add graceful shutdown hooks and metrics.
        """
        while True:
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error during decision loop: %s", exc)
            time.sleep(self.settings.poll_interval_seconds)
