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
