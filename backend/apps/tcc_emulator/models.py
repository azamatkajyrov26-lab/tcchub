from django.conf import settings
from django.db import models


class EmulatedDataSource(models.Model):
    """Эмулятор закрытых источников данных (КТЖ, ОТЛК, Порт Актау)"""

    EMULATION_STRATEGIES = [
        ("static_expert", "Статические экспертные данные"),
        ("parametric", "Параметрическая генерация"),
        ("historical_based", "На основе исторических данных"),
        ("ai_generated", "AI-генерация"),
    ]

    data_source = models.OneToOneField(
        "tcc_data.DataSource",
        on_delete=models.CASCADE,
        related_name="emulation_config",
        verbose_name="Источник данных",
    )
    emulation_strategy = models.CharField(
        "Стратегия эмуляции", max_length=20, choices=EMULATION_STRATEGIES
    )
    base_parameters = models.JSONField("Базовые параметры", default=dict, blank=True)
    variance_config = models.JSONField("Конфигурация отклонений", default=dict, blank=True)

    confidence_level = models.FloatField("Уровень достоверности (0-1)", default=0.7)
    data_age_days = models.IntegerField("Возраст данных (дней)", default=90)
    source_references = models.JSONField("Источники-основания", default=list, blank=True)

    disclaimer_ru = models.TextField(
        "Дисклеймер (RU)",
        default="Данные эмулированы на основе экспертных оценок и публичных отчётов.",
    )
    last_reviewed = models.DateField("Последний пересмотр", null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Проверил",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Эмулируемый источник"
        verbose_name_plural = "Эмулируемые источники"

    def __str__(self):
        return f"Эмуляция: {self.data_source.name}"


class EmulatedNodeStatus(models.Model):
    """Эмулированные статусы узлов (КПП, порты без API)"""

    node = models.ForeignKey(
        "tcc_core.RouteNode",
        on_delete=models.CASCADE,
        related_name="emulated_statuses",
        verbose_name="Узел",
    )
    emulation_source = models.ForeignKey(
        EmulatedDataSource,
        on_delete=models.CASCADE,
        related_name="node_statuses",
        verbose_name="Источник эмуляции",
    )
    date = models.DateField("Дата")
    throughput_percent = models.IntegerField("Загрузка (%)")
    avg_wait_hours = models.FloatField("Среднее ожидание (часы)")
    incidents_count = models.IntegerField("Инцидентов", default=0)
    note = models.TextField("Примечание", blank=True)
    is_emulated = models.BooleanField("Эмулировано", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Статус узла (эмуляция)"
        verbose_name_plural = "Статусы узлов (эмуляция)"
        ordering = ["-date"]
        unique_together = ["node", "date"]

    def __str__(self):
        return f"{self.node.name_en} @ {self.date} — {self.throughput_percent}%"
