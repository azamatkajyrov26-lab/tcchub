from django.conf import settings
from django.db import models


class Alert(models.Model):
    ALERT_TYPES = [
        ("risk_change", "Изменение риска"),
        ("node_status", "Статус узла"),
        ("sanction_update", "Обновление санкций"),
        ("score_threshold", "Порог оценки"),
        ("news_critical", "Критические новости"),
    ]

    SEVERITY_LEVELS = [
        ("info", "Информация"),
        ("warning", "Предупреждение"),
        ("critical", "Критический"),
    ]

    alert_type = models.CharField(
        "Тип оповещения", max_length=50, choices=ALERT_TYPES
    )
    severity = models.CharField(
        "Серьёзность", max_length=20, choices=SEVERITY_LEVELS
    )
    title = models.CharField("Заголовок", max_length=500)
    description = models.TextField("Описание")

    corridor = models.ForeignKey(
        "tcc_core.TradeCorridor",
        on_delete=models.CASCADE,
        verbose_name="Коридор",
        null=True,
        blank=True,
        related_name="alerts",
    )
    country = models.ForeignKey(
        "tcc_core.Country",
        on_delete=models.CASCADE,
        verbose_name="Страна",
        null=True,
        blank=True,
        related_name="alerts",
    )
    node = models.ForeignKey(
        "tcc_core.RouteNode",
        on_delete=models.CASCADE,
        verbose_name="Узел маршрута",
        null=True,
        blank=True,
        related_name="alerts",
    )
    related_score = models.ForeignKey(
        "tcc_intelligence.RouteScore",
        on_delete=models.SET_NULL,
        verbose_name="Связанная оценка",
        null=True,
        blank=True,
        related_name="alerts",
    )

    is_resolved = models.BooleanField("Решено", default=False)
    resolved_at = models.DateTimeField("Дата решения", null=True, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    data = models.JSONField("Дополнительные данные", default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Оповещение"
        verbose_name_plural = "Оповещения"
        indexes = [
            models.Index(fields=["alert_type"], name="idx_alert_type"),
            models.Index(fields=["severity"], name="idx_alert_severity"),
            models.Index(fields=["is_resolved"], name="idx_alert_resolved"),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class AlertSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="alert_subscriptions",
    )
    corridor = models.ForeignKey(
        "tcc_core.TradeCorridor",
        on_delete=models.CASCADE,
        verbose_name="Коридор",
        null=True,
        blank=True,
        related_name="alert_subscriptions",
    )
    alert_types = models.JSONField(
        "Типы оповещений",
        default=list,
        blank=True,
        help_text="Список кодов типов оповещений для подписки",
    )
    email_enabled = models.BooleanField("Email уведомления", default=True)
    web_enabled = models.BooleanField("Web уведомления", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Подписка на оповещения"
        verbose_name_plural = "Подписки на оповещения"
        unique_together = ["user", "corridor"]

    def __str__(self):
        corridor_name = self.corridor.name if self.corridor else "Все коридоры"
        return f"{self.user} — {corridor_name}"
