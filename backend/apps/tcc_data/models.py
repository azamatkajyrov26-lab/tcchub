from django.conf import settings
from django.db import models


class DataSource(models.Model):
    """Реестр всех источников данных"""

    SOURCE_TYPES = [
        ("api_public", "Публичный API"),
        ("api_private", "Приватный API (партнёрство)"),
        ("file_xml", "XML файл"),
        ("file_csv", "CSV файл"),
        ("rss", "RSS лента"),
        ("scraping", "Парсинг сайта"),
        ("manual", "Ручной ввод"),
        ("emulated", "Эмуляция"),
    ]
    ACCESS_STATUSES = [
        ("available", "Доступен"),
        ("pending_partnership", "Ожидает партнёрства"),
        ("negotiating", "На переговорах"),
        ("emulated", "Эмулируется"),
        ("blocked", "Недоступен"),
    ]

    name = models.CharField("Название", max_length=300)
    code = models.CharField("Код", max_length=100, unique=True)
    source_type = models.CharField(
        "Тип источника", max_length=20, choices=SOURCE_TYPES
    )
    base_url = models.URLField("Базовый URL", blank=True)
    api_key_env = models.CharField(
        "ENV переменная API ключа", max_length=100, blank=True
    )
    fetch_interval_hours = models.IntegerField(
        "Интервал обновления (часы)", default=24
    )
    is_active = models.BooleanField("Активен", default=True)
    access_status = models.CharField(
        "Статус доступа",
        max_length=30,
        choices=ACCESS_STATUSES,
        default="available",
    )
    last_sync = models.DateTimeField("Последняя синхронизация", null=True, blank=True)
    last_sync_status = models.CharField(
        "Статус последней синхронизации", max_length=50, default="never"
    )
    records_count = models.IntegerField("Записей в базе", default=0)
    notes = models.TextField("Заметки", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Источник данных"
        verbose_name_plural = "Источники данных"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class SyncLog(models.Model):
    """Лог синхронизации источника данных"""

    STATUS_CHOICES = [
        ("running", "Выполняется"),
        ("success", "Успех"),
        ("partial", "Частично"),
        ("failed", "Ошибка"),
    ]

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="sync_logs",
        verbose_name="Источник",
    )
    started_at = models.DateTimeField("Начало", auto_now_add=True)
    finished_at = models.DateTimeField("Окончание", null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES)
    records_fetched = models.IntegerField("Получено записей", default=0)
    records_new = models.IntegerField("Новых записей", default=0)
    records_updated = models.IntegerField("Обновлено записей", default=0)
    error_message = models.TextField("Сообщение об ошибке", blank=True)
    celery_task_id = models.CharField(
        "Celery Task ID", max_length=200, blank=True
    )

    class Meta:
        verbose_name = "Лог синхронизации"
        verbose_name_plural = "Логи синхронизаций"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.source.code} — {self.started_at:%Y-%m-%d %H:%M} — {self.status}"


class SanctionEntry(models.Model):
    """Записи из OFAC, EU, UN санкционных списков"""

    ENTITY_TYPES = [
        ("individual", "Физлицо"),
        ("company", "Компания"),
        ("vessel", "Судно"),
        ("aircraft", "Самолёт"),
    ]

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="sanction_entries",
        verbose_name="Источник",
    )
    external_id = models.CharField("Внешний ID", max_length=200)
    entity_type = models.CharField(
        "Тип сущности", max_length=20, choices=ENTITY_TYPES
    )
    name_primary = models.CharField("Основное имя", max_length=500)
    name_aliases = models.JSONField("Псевдонимы", default=list, blank=True)
    countries = models.JSONField("Страны (ISO2)", default=list, blank=True)
    program = models.CharField("Программа санкций", max_length=300, blank=True)
    listing_date = models.DateField("Дата включения", null=True, blank=True)
    raw_data = models.JSONField("Сырые данные", default=dict, blank=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Санкционная запись"
        verbose_name_plural = "Санкционные записи"
        unique_together = ["source", "external_id"]
        indexes = [
            models.Index(fields=["name_primary"]),
            models.Index(fields=["entity_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name_primary} ({self.source.code})"


class TradeFlow(models.Model):
    """Торговые потоки из UN Comtrade"""

    FLOW_TYPES = [
        ("import", "Импорт"),
        ("export", "Экспорт"),
    ]

    reporter_country = models.ForeignKey(
        "tcc_core.Country",
        on_delete=models.CASCADE,
        related_name="reported_flows",
        verbose_name="Страна-репортёр",
    )
    partner_country = models.ForeignKey(
        "tcc_core.Country",
        on_delete=models.CASCADE,
        related_name="partner_flows",
        verbose_name="Страна-партнёр",
    )
    year = models.IntegerField("Год")
    hs_code = models.CharField("HS код", max_length=10)
    flow_type = models.CharField("Тип потока", max_length=10, choices=FLOW_TYPES)
    value_usd = models.BigIntegerField("Стоимость (USD)")
    weight_kg = models.BigIntegerField("Вес (кг)", null=True, blank=True)
    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="trade_flows",
        verbose_name="Источник",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Торговый поток"
        verbose_name_plural = "Торговые потоки"
        unique_together = [
            "reporter_country",
            "partner_country",
            "year",
            "hs_code",
            "flow_type",
        ]
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["hs_code"]),
        ]

    def __str__(self):
        return f"{self.reporter_country.iso2}→{self.partner_country.iso2} {self.hs_code} {self.year}"


class NewsItem(models.Model):
    """Новостные записи с AI-аннотацией"""

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="news_items",
        verbose_name="Источник",
    )
    external_id = models.CharField("Внешний ID", max_length=500, blank=True)
    title = models.CharField("Заголовок", max_length=1000)
    content = models.TextField("Содержание")
    url = models.URLField("URL", max_length=2000, blank=True)
    published_at = models.DateTimeField("Дата публикации")
    language = models.CharField("Язык", max_length=10, default="en")
    # AI-аннотация
    ai_processed = models.BooleanField("AI обработано", default=False)
    ai_risk_type = models.CharField("AI тип риска", max_length=100, blank=True)
    ai_severity = models.IntegerField("AI серьёзность (1-10)", null=True, blank=True)
    ai_affected_countries = models.JSONField(
        "AI затронутые страны", default=list, blank=True
    )
    ai_affected_corridors = models.JSONField(
        "AI затронутые коридоры", default=list, blank=True
    )
    ai_summary_ru = models.TextField("AI резюме (RU)", blank=True)
    ai_is_relevant = models.BooleanField("AI релевантна", null=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        unique_together = ["source", "external_id"]
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["ai_processed"]),
            models.Index(fields=["ai_severity"]),
        ]

    def __str__(self):
        return self.title[:80]
