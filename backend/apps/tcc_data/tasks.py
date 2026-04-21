import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_ofac_sanctions(self):
    """Скачивает OFAC SDN XML, парсит, обновляет SanctionEntry"""
    from .fetchers.ofac import fetch_ofac_sdn
    from .models import DataSource, SyncLog

    source, _ = DataSource.objects.get_or_create(
        code="OFAC_SDN",
        defaults={
            "name": "OFAC SDN List",
            "source_type": "file_xml",
            "base_url": "https://www.treasury.gov/ofac/downloads/sdn.xml",
            "fetch_interval_hours": 24,
        },
    )

    log = SyncLog.objects.create(
        source=source,
        status="running",
        celery_task_id=self.request.id or "",
    )

    try:
        result = fetch_ofac_sdn(source, log)
        log.status = "success"
        log.records_fetched = result["fetched"]
        log.records_new = result["new"]
        log.records_updated = result["updated"]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.records_count = source.sanction_entries.filter(is_active=True).count()
        source.save()

        logger.info(
            "OFAC sync complete: %d fetched, %d new, %d updated",
            result["fetched"], result["new"], result["updated"],
        )
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)[:2000]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync_status = "failed"
        source.save()

        logger.error("OFAC sync failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_eu_sanctions(self):
    """Скачивает EU Consolidated Sanctions XML"""
    from .fetchers.eu_sanctions import fetch_eu_sanctions
    from .models import DataSource, SyncLog

    source, _ = DataSource.objects.get_or_create(
        code="EU_SANCTIONS",
        defaults={
            "name": "EU Consolidated Sanctions",
            "source_type": "file_xml",
            "base_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content",
            "fetch_interval_hours": 24,
        },
    )

    log = SyncLog.objects.create(
        source=source,
        status="running",
        celery_task_id=self.request.id or "",
    )

    try:
        result = fetch_eu_sanctions(source, log)
        log.status = "success"
        log.records_fetched = result["fetched"]
        log.records_new = result["new"]
        log.records_updated = result["updated"]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.records_count = source.sanction_entries.filter(is_active=True).count()
        source.save()
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)[:2000]
        log.finished_at = timezone.now()
        log.save()
        source.last_sync_status = "failed"
        source.save()
        logger.error("EU sanctions sync failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_un_sanctions(self):
    """Скачивает UN Consolidated Sanctions XML"""
    from .fetchers.un_sanctions import fetch_un_sanctions
    from .models import DataSource, SyncLog

    source, _ = DataSource.objects.get_or_create(
        code="UN_SANCTIONS",
        defaults={
            "name": "UN Security Council Sanctions",
            "source_type": "file_xml",
            "base_url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
            "fetch_interval_hours": 24,
        },
    )

    log = SyncLog.objects.create(
        source=source,
        status="running",
        celery_task_id=self.request.id or "",
    )

    try:
        result = fetch_un_sanctions(source, log)
        log.status = "success"
        log.records_fetched = result["fetched"]
        log.records_new = result["new"]
        log.records_updated = result["updated"]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.records_count = source.sanction_entries.filter(is_active=True).count()
        source.save()
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)[:2000]
        log.finished_at = timezone.now()
        log.save()
        source.last_sync_status = "failed"
        source.save()
        logger.error("UN sanctions sync failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_worldbank_indicators(self):
    """Загружает индикаторы World Bank для стран коридоров"""
    from .fetchers.worldbank import fetch_worldbank_indicators
    from .models import DataSource, SyncLog

    source, _ = DataSource.objects.get_or_create(
        code="WORLD_BANK",
        defaults={
            "name": "World Bank Open Data",
            "source_type": "api_public",
            "base_url": "https://api.worldbank.org/v2/",
            "fetch_interval_hours": 168,
        },
    )

    log = SyncLog.objects.create(
        source=source,
        status="running",
        celery_task_id=self.request.id or "",
    )

    try:
        result = fetch_worldbank_indicators(source, log)
        log.status = "success"
        log.records_fetched = result["fetched"]
        log.records_updated = result["updated"]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.save()

        logger.info("World Bank sync complete: %d updated", result["updated"])
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)[:2000]
        log.finished_at = timezone.now()
        log.save()
        source.last_sync_status = "failed"
        source.save()
        logger.error("World Bank sync failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_and_annotate_news(self):
    """Загружает новости с NewsAPI и сохраняет в базу"""
    from .fetchers.news_api import fetch_news
    from .models import DataSource, SyncLog

    source, _ = DataSource.objects.get_or_create(
        code="NEWS_API",
        defaults={
            "name": "NewsAPI",
            "source_type": "api_public",
            "base_url": "https://newsapi.org/v2/",
            "fetch_interval_hours": 2,
        },
    )

    log = SyncLog.objects.create(
        source=source,
        status="running",
        celery_task_id=self.request.id or "",
    )

    try:
        result = fetch_news(source, log)
        log.status = "success"
        log.records_fetched = result["fetched"]
        log.records_new = result["new"]
        log.finished_at = timezone.now()
        log.save()

        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.records_count = source.news_items.count()
        source.save()

        logger.info("News fetch complete: %d fetched, %d new", result["fetched"], result["new"])
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)[:2000]
        log.finished_at = timezone.now()
        log.save()
        source.last_sync_status = "failed"
        source.save()
        logger.error("News fetch failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def fetch_rss_news(self):
    """Парсит новости из RSS-лент логистических изданий (каждые 6 часов)"""
    from .fetchers.rss_feeds import fetch_all_rss_feeds

    try:
        result = fetch_all_rss_feeds()
        logger.info(
            "RSS news fetch: %d sources, %d new articles",
            result["sources"], result["total_new"],
        )
    except Exception as exc:
        logger.error("RSS news fetch failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def scrape_and_analyze_with_groq(self):
    """
    1. Scrape full article text (newspaper4k)
    2. Analyze with Groq Llama 3 — corridor impact score, type, Russian summary
    3. Export analyzed articles to Obsidian vault (.md files)
    Processes up to 20 articles per run to stay within Groq free limits.
    """
    import os, json, re, pathlib
    from .models import NewsItem

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        logger.warning("GROQ_API_KEY not set, skipping Groq analysis")
        return {"analyzed": 0, "skipped": 0, "reason": "no_api_key"}

    import requests as _req

    def groq_analyze(text: str) -> dict:
        """Call Groq API via requests (more reliable than groq package)."""
        resp = _req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
                "max_tokens": 400,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    # newspaper4k for scraping full text
    try:
        import newspaper
        HAS_NEWSPAPER = True
    except ImportError:
        HAS_NEWSPAPER = False
        logger.warning("newspaper4k not installed, will use existing content")

    # Obsidian vault directory
    vault_dir = pathlib.Path("/opt/tcchub/obsidian-vault/Новости")
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Find unprocessed items with a URL
    items = NewsItem.objects.filter(
        groq_processed=False,
        url__startswith="http",
    ).order_by("-published_at")[:20]

    analyzed = 0
    skipped = 0

    SYSTEM_PROMPT = """Ты — аналитик логистики Транскаспийского (Среднего) коридора.
Твоя задача: оценить как новость влияет на грузовые перевозки через Средний коридор
(Казахстан → Каспий → Азербайджан → Грузия → Турция/Европа).

Верни JSON со следующими полями:
- score: число 0-10 (0=нерелевантно, 10=критически важно для коридора)
- impact_type: один из [задержка, инфраструктура, тариф, санкция, объём, риск, прочее]
- affected_nodes: массив из названий затронутых узлов ["Актау", "Баку", "Хоргос" и т.д.]
- summary_ru: 2-3 предложения на русском — что произошло и как это влияет на Средний коридор
- is_relevant: true если score >= 4, false если нет

Отвечай ТОЛЬКО JSON без дополнительного текста."""

    for item in items:
        try:
            # Step 1: Get full article text
            article_text = item.content or ""
            if HAS_NEWSPAPER and item.url and len(article_text) < 500:
                try:
                    art = newspaper.Article(item.url, language="en")
                    art.download()
                    art.parse()
                    if art.text and len(art.text) > 100:
                        article_text = art.text
                        item.full_content = article_text[:20000]
                except Exception as e:
                    logger.debug("Newspaper scrape failed for %s: %s", item.url, e)

            # Limit text for Groq
            text_for_groq = (item.title + "\n\n" + article_text)[:3000]

            # Step 2: Groq analysis via requests
            raw = groq_analyze(f"Заголовок: {item.title}\n\nТекст: {article_text[:2500]}")
            data = json.loads(raw)

            item.groq_score = float(data.get("score", 0))
            item.groq_impact_type = str(data.get("impact_type", "прочее"))[:100]
            item.groq_affected_nodes = data.get("affected_nodes", [])
            item.groq_summary_ru = str(data.get("summary_ru", ""))[:2000]
            item.ai_is_relevant = bool(data.get("is_relevant", item.groq_score >= 4))
            item.groq_processed = True
            item.save(update_fields=[
                "full_content", "groq_score", "groq_impact_type",
                "groq_affected_nodes", "groq_summary_ru", "ai_is_relevant", "groq_processed"
            ])

            # Step 3: Write to Obsidian vault
            if item.groq_score and item.groq_score >= 4:
                _write_obsidian_note(item, vault_dir)

            analyzed += 1

        except json.JSONDecodeError as e:
            logger.warning("Groq JSON parse error for #%s: %s", item.pk, e)
            item.groq_processed = True
            item.save(update_fields=["groq_processed"])
            skipped += 1
        except Exception as e:
            logger.warning("Groq analysis error for #%s: %s", item.pk, e)
            skipped += 1

    logger.info("Groq analysis: %d analyzed, %d skipped", analyzed, skipped)
    return {"analyzed": analyzed, "skipped": skipped}


def _write_obsidian_note(item, vault_dir):
    """Write a NewsItem to Obsidian vault as a markdown note."""
    import re, pathlib
    from django.utils.timezone import localtime

    safe_title = re.sub(r'[\\/*?"<>|:]', '', item.title)[:80].strip()
    date_str = localtime(item.published_at).strftime("%Y-%m-%d")
    filename = f"{date_str}-{safe_title}.md"
    filepath = vault_dir / filename

    score = item.groq_score or 0
    score_bar = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"
    nodes = ", ".join(f"[[{n}]]" for n in (item.groq_affected_nodes or []))

    content = f"""---
title: "{item.title}"
date: {date_str}
source: {item.source.name if item.source else "Unknown"}
url: "{item.url}"
corridor_score: {score:.1f}
impact_type: {item.groq_impact_type or "прочее"}
affected_nodes: {item.groq_affected_nodes or []}
tags:
  - новость
  - {item.groq_impact_type or "прочее"}
  - средний-коридор
---

## {item.title}

> **{score_bar} Влияние на Средний коридор: {score:.0f}/10** — {item.groq_impact_type}

**Источник:** [{item.source.name if item.source else "N/A"}]({item.url})
**Дата:** {date_str}

{f"**Затронутые узлы:** {nodes}" if nodes else ""}

### Вывод ИИ

{item.groq_summary_ru or "Анализ не выполнен"}

---

### Оригинальный текст

{item.full_content or item.content or "Полный текст недоступен"}
"""
    try:
        filepath.write_text(content, encoding="utf-8")
        logger.debug("Obsidian note written: %s", filename)
    except Exception as e:
        logger.warning("Failed to write Obsidian note: %s", e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def translate_news_to_russian(self):
    """
    Translate untranslated English news titles and summaries to Russian.
    Uses deep-translator (Google Translate, free, no API key).
    Processes up to 50 items per run to avoid rate limits.
    """
    from .models import NewsItem

    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        logger.warning("deep-translator not installed, skipping translation")
        return {"translated": 0, "skipped": 0}

    translator = GoogleTranslator(source="en", target="ru")

    # Find English news without Russian summary
    items = NewsItem.objects.filter(
        language="en",
        ai_summary_ru="",
        ai_processed=False,
    ).order_by("-published_at")[:50]

    translated = 0
    skipped = 0

    for item in items:
        try:
            # Translate title (keep original, add RU version to summary)
            text_to_translate = item.title
            if item.content and len(item.content) > 20:
                # Translate first 300 chars of content as summary
                snippet = item.content[:300].strip()
                text_to_translate = f"{item.title}\n\n{snippet}"

            # Google Translate has ~5000 char limit per request
            if len(text_to_translate) > 4800:
                text_to_translate = text_to_translate[:4800]

            ru_text = translator.translate(text_to_translate)

            item.ai_summary_ru = ru_text or ""
            item.ai_processed = True
            item.save(update_fields=["ai_summary_ru", "ai_processed"])
            translated += 1

        except Exception as e:
            logger.warning("Translation failed for news #%s: %s", item.pk, e)
            # Mark as processed to avoid retry loops on broken items
            item.ai_processed = True
            item.save(update_fields=["ai_processed"])
            skipped += 1

    logger.info("Translation task: %d translated, %d skipped", translated, skipped)
    return {"translated": translated, "skipped": skipped}
