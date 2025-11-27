"""Service to gather news headlines via the configured client."""

import logging
from typing import List

from src.clients.news_client import NewsClient
from src.data.models import NewsHeadline

logger = logging.getLogger(__name__)


class NewsService:
    """Lightweight façade over the news client."""

    def __init__(self, client: NewsClient):
        self.client = client

    def fetch(self, max_headlines: int) -> List[NewsHeadline]:
        """
        Fetch the latest headlines.

        Returns an empty list when news is disabled or the provider is missing.
        """
        logger.info("Fetching news headlines (limit=%s)", max_headlines)
        try:
            return self.client.fetch_headlines(limit=max_headlines)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch news headlines: %s", exc)
            return []
