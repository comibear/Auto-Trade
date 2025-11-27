"""Placeholder client for fetching news headlines from external providers."""

import logging
from datetime import datetime
from typing import List, Optional

from src.data.models import NewsHeadline

logger = logging.getLogger(__name__)


class NewsClient:
    """Fetches news headlines from a configurable provider."""

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.provider = provider
        self.api_key = api_key

    def fetch_headlines(self, limit: int = 10) -> List[NewsHeadline]:
        """
        Retrieve headlines from the configured provider.

        TODO: wire to a real news API when provider and authentication are finalized.
        """
        logger.info("News collection requested (provider=%s, limit=%s)", self.provider, limit)
        if not self.provider:
            logger.warning("No news provider configured; returning an empty headline list.")
            return []

        # Placeholder data to demonstrate the schema.
        return [
            NewsHeadline(
                title="Sample headline placeholder",
                source=self.provider,
                url=None,
                published_at=datetime.utcnow(),
                summary="TODO: Replace with real news content.",
                tags=[],
            )
        ]
