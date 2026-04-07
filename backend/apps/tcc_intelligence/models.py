from django.conf import settings
from django.db import models


class RiskFactor(models.Model):
    """Конкретный риск-фактор для коридора/страны/узла"""

    RISK_CATEGORIES = [
        ("sanctions", "Санкции"),
        ("geopolitical", "Геополитика"),
        ("infrastructure", "Инфраструктура"),
        ("regulatory", "Регулирование"),
        ("financial", "Финансовый"),
        ("operational", "Операционный"),
    ]
    SOURCE_TYPES = [
        ("auto_sanction", "Авто: санкции"),
        ("auto_news", "Авто: новости"),
        ("auto_worldbank", "Авто: World Bank"),
        ("manual_analyst", "Аналитик TCC"),
    ]

    corridor = models.ForeignKey(
        "tcc_core.TradeCorridor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="risk_factors",
        verbose_name="Коридор",
    )
    country = models.ForeignKey(
        "tcc_core.Country",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="risk_factors",
        verbose_name="Страна",
    )
    node = models.ForeignKey(
        "tcc_core.RouteNode",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="risk_factors",
        verbose_name="Узел",
    )

    risk_category = models.CharField(
        "Категория риска", max_length=20, choices=RISK_CATEGORIES
    )
    severity = models.IntegerField("Серьёзность (1-10)")
    probability = models.IntegerField("Вероятность (1-10)")
    impact_score = models.FloatField("Импакт-скор")

    title = models.CharField("Заголовок", max_length=500)
    description = models.TextField("Описание")
    evidence = models.TextField("Доказательства", blank=True)
    mitigation = models.TextField("Меры снижения", blank=True)

    source_type = models.CharField(
        "Тип источника", max_length=20, choices=SOURCE_TYPES
    )
    news_item = models.ForeignKey(
        "tcc_data.NewsItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="risk_factors",
        verbose_name="Новость",
    )

    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует до", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Риск-фактор"
        verbose_name_plural = "Риск-факторы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["risk_category"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.impact_score = self.severity * self.probability / 10.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_risk_category_display()})"


class RouteScore(models.Model):
    """Итоговый скор маршрута — рассчитывается автоматически"""

    RISK_LEVELS = [
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
        ("critical", "Критический"),
    ]

    corridor = models.ForeignKey(
        "tcc_core.TradeCorridor",
        on_delete=models.CASCADE,
        related_name="route_scores",
        verbose_name="Коридор",
    )
    calculated_at = models.DateTimeField("Рассчитан", auto_now_add=True)

    score_sanctions = models.FloatField("Скор: санкции", default=0)
    score_geopolitical = models.FloatField("Скор: геополитика", default=0)
    score_infrastructure = models.FloatField("Скор: инфраструктура", default=0)
    score_regulatory = models.FloatField("Скор: регулирование", default=0)
    score_financial = models.FloatField("Скор: финансы", default=0)
    score_total = models.FloatField("Общий скор", default=0)

    risk_level = models.CharField(
        "Уровень риска", max_length=20, choices=RISK_LEVELS
    )
    weights = models.JSONField("Веса", default=dict)
    factors_snapshot = models.JSONField("Снимок факторов", default=list)

    class Meta:
        verbose_name = "Скор маршрута"
        verbose_name_plural = "Скоры маршрутов"
        ordering = ["-calculated_at"]

    def __str__(self):
        return f"{self.corridor.code} — {self.score_total:.2f} ({self.risk_level}) @ {self.calculated_at:%Y-%m-%d}"


class Scenario(models.Model):
    """Сценарий для маршрута: Plan A / B / C"""

    corridor = models.ForeignKey(
        "tcc_core.TradeCorridor",
        on_delete=models.CASCADE,
        related_name="scenarios",
        verbose_name="Коридор",
    )
    label = models.CharField("Название", max_length=100)
    plan_code = models.CharField("Код плана", max_length=10)
    description = models.TextField("Описание")

    cost_index = models.FloatField("Индекс стоимости")
    transit_days_min = models.IntegerField("Транзит дней (мин)")
    transit_days_max = models.IntegerField("Транзит дней (макс)")
    reliability_score = models.FloatField("Надёжность (0-1)")
    risk_score = models.FloatField("Риск (0-1)")

    alternative_nodes = models.ManyToManyField(
        "tcc_core.RouteNode",
        blank=True,
        verbose_name="Альтернативные узлы",
    )
    notes = models.TextField("Заметки", blank=True)

    is_recommended = models.BooleanField("Рекомендован", default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Сценарий"
        verbose_name_plural = "Сценарии"
        ordering = ["corridor", "plan_code"]

    def __str__(self):
        return f"{self.corridor.code} — Plan {self.plan_code}: {self.label}"
