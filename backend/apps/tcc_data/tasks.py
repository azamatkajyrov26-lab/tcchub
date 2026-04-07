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
