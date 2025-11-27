"""Entrypoint for the automated trading pipeline."""

import logging
import os

from src.agent.llm_client import LLMClient
from src.clients.hyperliquid_client import HyperliquidClient
from src.clients.news_client import NewsClient
from src.config.settings import AppSettings
from src.data.market_data_service import MarketDataService
from src.data.news_service import NewsService
from src.services.decision_loop import DecisionLoop
from src.trading.risk_management import RiskManager
from src.trading.trade_executor import TradeExecutor


def configure_logging() -> None:
    """Set a simple logging format for local development."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def build_decision_loop(settings: AppSettings) -> DecisionLoop:
    """Wire together dependencies required for the decision loop."""
    hl_client = HyperliquidClient(
        base_url=settings.hyperliquid.base_url,
        skip_ws=settings.hyperliquid.skip_ws,
        perp_dexs=settings.hyperliquid.perp_dexs,
    )
    # Fetch enough candles for indicators (RSI14 needs at least 15); we display the last 10.
    market_service = MarketDataService(client=hl_client, candle_limit=50)

    news_service = None
    if settings.news.enabled:
        news_client = NewsClient(provider=settings.news.provider, api_key=settings.news.api_key)
        news_service = NewsService(client=news_client)

    llm_client = LLMClient(
        provider=settings.llm.provider,
        api_key=settings.llm.api_key,
        model=settings.llm.model,
    )
    risk_manager = RiskManager(settings=settings.risk)
    executor = TradeExecutor(client=hl_client, risk_manager=risk_manager, risk_settings=settings.risk)

    return DecisionLoop(
        settings=settings,
        market_data=market_service,
        llm_client=llm_client,
        executor=executor,
        news_service=news_service,
    )


def main() -> None:
    """Initialize settings and start the trading loop."""
    configure_logging()
    settings = AppSettings.from_env()
    decision_loop = build_decision_loop(settings)
    run_once = os.getenv("RUN_ONCE", "true").lower() == "true"
    if run_once:
        decision_loop.run_once()
    else:
        decision_loop.run_forever()


if __name__ == "__main__":
    main()
