"""
RSS/Atom fetcher for logistics & Middle Corridor news.
Parses real news from multiple international sources daily.
No API key required — uses public RSS feeds.
"""

import hashlib
import logging
from datetime import datetime, timezone as dt_tz
from email.utils import parsedate_to_datetime

import requests
from lxml import etree

from apps.tcc_data.models import DataSource, NewsItem

logger = logging.getLogger(__name__)

# ── RSS Feed Sources ─────────────────────────────────────────
# Each source: (code, name, rss_url, language, keywords_filter)
# keywords_filter: if non-empty, only keep items whose title/desc match any keyword
RSS_SOURCES = [
    (
        "LOADSTAR",
        "The Loadstar",
        "https://theloadstar.com/feed/",
        "en",
        [],  # all articles are logistics-relevant
    ),
    (
        "FREIGHTWAVES",
        "FreightWaves",
        "https://www.freightwaves.com/feed",
        "en",
        ["corridor", "caspian", "central asia", "silk road", "kazakh",
         "TMTM", "BRI", "belt and road", "eurasia", "turkey", "georgia",
         "azerbaijan", "china rail", "container", "freight", "port"],
    ),
    (
        "SUPPLYCHAINDIVE",
        "Supply Chain Dive",
        "https://www.supplychaindive.com/feeds/news/",
        "en",
        ["corridor", "silk road", "eurasia", "trade route", "logistics",
         "freight", "container", "port", "railway", "supply chain"],
    ),
    (
        "GCAPTAIN",
        "gCaptain",
        "https://gcaptain.com/feed/",
        "en",
        ["caspian", "black sea", "suez", "corridor", "turkey", "strait",
         "container", "freight", "port", "shipping", "trade"],
    ),
    (
        "RAILFREIGHT",
        "RailFreight.com",
        "https://www.railfreight.com/feed/",
        "en",
        [],  # rail freight is directly relevant
    ),
    (
        "SEANEWS_TR",
        "SeaNews Turkey",
        "https://www.seanews.com.tr/rss/",
        "en",
        ["corridor", "caspian", "baku", "turkey", "georgia", "kazakh",
         "container", "port", "freight", "logistics"],
    ),
    (
        "INFORM_KZ",
        "Inform.kz",
        "https://www.inform.kz/rss/",
        "ru",
        ["логистик", "транспорт", "коридор", "груз", "железнодорож", "порт",
         "торговл", "КТЖ", "Актау", "Курык", "транзит", "маршрут"],
    ),
    (
        "SPLASH247",
        "Splash247 Maritime",
        "https://splash247.com/feed/",
        "en",
        ["corridor", "caspian", "silk road", "central asia", "kazakh",
         "turkey", "black sea", "suez", "container", "freight", "BRI"],
    ),
    (
        "CONTAINER_NEWS",
        "Container News",
        "https://container-news.com/feed/",
        "en",
        ["corridor", "caspian", "silk road", "eurasia", "kazakh", "BRI",
         "turkey", "container", "freight", "rail", "port"],
    ),
    (
        "RAILWAY_GAZETTE",
        "Railway Gazette",
        "https://www.railwaygazette.com/feed",
        "en",
        ["corridor", "caspian", "central asia", "silk road", "kazakh",
         "TMTM", "BRI", "georgia", "azerbaijan", "china rail", "transit"],
    ),
    (
        "ASTANA_TIMES",
        "Astana Times",
        "https://astanatimes.com/feed/",
        "en",
        [],  # Kazakhstan-focused, all articles relevant
    ),
    (
        "ADB",
        "Asian Development Bank",
        "https://www.adb.org/rss.xml",
        "en",
        ["corridor", "caspian", "central asia", "kazakhstan", "transport",
         "infrastructure", "logistics", "connectivity", "BRI", "silk road",
         "uzbekistan", "kyrgyzstan", "tajikistan", "CAREC"],
    ),
    (
        "KAPITAL_KZ",
        "Kapital.kz",
        "https://kapital.kz/rss.xml",
        "ru",
        ["логистик", "транспорт", "коридор", "груз", "железнодорож",
         "порт", "КТЖ", "Актау", "транзит", "ТМТМ", "маршрут", "экспорт"],
    ),
    (
        "KAZPRAVDA",
        "Казахстанская правда",
        "https://www.kazpravda.kz/rss/",
        "ru",
        ["логистик", "транспорт", "коридор", "груз", "железнодорож",
         "порт", "КТЖ", "транзит", "ТМТМ", "экспорт", "торговл"],
    ),
]

# Request headers
HEADERS = {
    "User-Agent": "TCC-Hub-NewsBot/1.0 (https://tc-cargo.kz; info@tc-cargo.kz)",
    "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml",
}

REQUEST_TIMEOUT = 20


def _make_id(url: str, title: str) -> str:
    """Generate a deterministic external_id from URL or title."""
    raw = url or title
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]


def _parse_date(date_str: str) -> datetime:
    """Try to parse RSS date string into a timezone-aware datetime."""
    if not date_str:
        return datetime.now(dt_tz.utc)
    # Try RFC 2822 (standard RSS)
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    # Try ISO 8601 (Atom)
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        pass
    return datetime.now(dt_tz.utc)


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    if not keywords:
        return True
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


import re as _re

def _strip_html(text: str) -> str:
    """Strip HTML tags and decode basic entities."""
    text = _re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#8217;', "'") \
               .replace('&#8216;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
    return _re.sub(r'\s+', ' ', text).strip()


def _parse_rss_xml(xml_bytes: bytes) -> list[dict]:
    """Parse RSS 2.0 or Atom XML into a list of article dicts."""
    items = []
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        # Try to recover
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml_bytes, parser=parser)

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    # RSS 2.0: //channel/item
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc_raw = (item.findtext("description") or "").strip()
        # Try content:encoded first for richer text
        ce = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        ce_text = (ce.text or "").strip() if ce is not None else ""
        # Pick the longer clean text between description and content:encoded
        desc_clean = _strip_html(desc_raw)
        ce_clean = _strip_html(ce_text)
        content = ce_clean if len(ce_clean) > len(desc_clean) else desc_clean
        pub_date = (item.findtext("pubDate") or "").strip()
        items.append({
            "title": title[:1000],
            "url": link[:2000],
            "content": content[:5000],
            "published_at": _parse_date(pub_date),
        })

    # Atom: //entry
    if not items:
        for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            title = ""
            title_el = entry.find("atom:title", ns) or entry.find("title")
            if title_el is not None and title_el.text:
                title = title_el.text.strip()

            link = ""
            link_el = entry.find("atom:link", ns) or entry.find("link")
            if link_el is not None:
                link = link_el.get("href", "").strip()

            desc = ""
            summary_el = (entry.find("atom:summary", ns)
                          or entry.find("atom:content", ns)
                          or entry.find("summary")
                          or entry.find("content"))
            if summary_el is not None and summary_el.text:
                desc = summary_el.text.strip()

            pub = ""
            pub_el = (entry.find("atom:published", ns)
                      or entry.find("atom:updated", ns)
                      or entry.find("published")
                      or entry.find("updated"))
            if pub_el is not None and pub_el.text:
                pub = pub_el.text.strip()

            items.append({
                "title": title[:1000],
                "url": link[:2000],
                "content": desc[:5000],
                "published_at": _parse_date(pub),
            })

    return items


def fetch_single_feed(
    code: str, name: str, rss_url: str, language: str, keywords: list[str]
) -> dict:
    """Fetch one RSS feed, filter by keywords, save to DB."""
    # Get or create DataSource
    source, _ = DataSource.objects.get_or_create(
        code=f"RSS_{code}",
        defaults={
            "name": name,
            "source_type": "rss",
            "base_url": rss_url,
            "fetch_interval_hours": 6,
        },
    )

    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("RSS fetch failed for %s: %s", code, e)
        return {"source": code, "fetched": 0, "new": 0}

    articles = _parse_rss_xml(resp.content)
    new_count = 0

    for article in articles:
        title = article["title"]
        content = article["content"]
        if not title:
            continue

        # Keyword filter
        combined_text = f"{title} {content}"
        if not _matches_keywords(combined_text, keywords):
            continue

        external_id = _make_id(article["url"], title)

        _, created = NewsItem.objects.get_or_create(
            source=source,
            external_id=external_id,
            defaults={
                "title": title,
                "content": content,
                "url": article["url"],
                "published_at": article["published_at"],
                "language": language,
            },
        )
        if created:
            new_count += 1

    # Update source stats
    from django.utils import timezone as tz
    source.last_sync = tz.now()
    source.last_sync_status = "success"
    source.records_count = source.news_items.count()
    source.save(update_fields=["last_sync", "last_sync_status", "records_count"])

    logger.info("RSS %s: %d articles, %d new", code, len(articles), new_count)
    return {"source": code, "fetched": len(articles), "new": new_count}


def fetch_all_rss_feeds() -> dict:
    """Fetch all configured RSS feeds. Returns summary."""
    results = []
    total_new = 0
    for code, name, url, lang, keywords in RSS_SOURCES:
        result = fetch_single_feed(code, name, url, lang, keywords)
        results.append(result)
        total_new += result["new"]

    logger.info("RSS fetch complete: %d sources, %d new articles", len(results), total_new)
    return {"sources": len(results), "total_new": total_new, "details": results}
