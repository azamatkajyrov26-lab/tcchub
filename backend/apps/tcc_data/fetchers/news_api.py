"""
Fetcher для NewsAPI.org — загружает новости по ключевым словам логистики/торговли.
"""

import logging
import os
from datetime import datetime, timedelta

import requests

from apps.tcc_data.models import DataSource, NewsItem

logger = logging.getLogger(__name__)

NEWS_API_URL = "https://newsapi.org/v2/everything"

KEYWORDS = (
    "(trade corridor OR Trans-Caspian OR Middle Corridor OR TMTM OR INSTC) "
    "AND (logistics OR sanctions OR transport OR cargo OR railway)"
)


def fetch_news(source, log):
    """Загружает новости с NewsAPI за последние 24 часа"""
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping news fetch")
        return {"fetched": 0, "new": 0, "updated": 0}

    from_date = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")

    try:
        resp = requests.get(
            NEWS_API_URL,
            params={
                "q": KEYWORDS,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 50,
                "apiKey": api_key,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("NewsAPI request failed: %s", e)
        return {"fetched": 0, "new": 0, "updated": 0}

    articles = data.get("articles", [])
    new_count = 0

    for article in articles:
        url = article.get("url", "")
        if not url:
            continue

        # Use URL as external_id for dedup
        external_id = url[:500]
        published_at = article.get("publishedAt")
        if published_at:
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                published_at = datetime.utcnow()
        else:
            published_at = datetime.utcnow()

        _, created = NewsItem.objects.get_or_create(
            source=source,
            external_id=external_id,
            defaults={
                "title": (article.get("title") or "")[:1000],
                "content": article.get("content") or article.get("description") or "",
                "url": url[:2000],
                "published_at": published_at,
                "language": "en",
            },
        )
        if created:
            new_count += 1

    return {"fetched": len(articles), "new": new_count, "updated": 0}
