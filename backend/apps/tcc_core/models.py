from django.db import models


class Region(models.Model):
    """Иерархия: Мир → Евразия → ЦА → Казахстан → Атырау"""

    REGION_TYPES = [
        ("continent", "Континент"),
        ("subcontinent", "Субконтинент"),
        ("country", "Страна"),
        ("region", "Регион"),
        ("city", "Город"),
    ]

    name = models.CharField("Название (RU)", max_length=200)
    name_en = models.CharField("Название (EN)", max_length=200, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родитель",
    )
    iso_code = models.CharField("ISO код", max_length=10, blank=True)
    region_type = models.CharField("Тип", max_length=20, choices=REGION_TYPES)
    coordinates = models.JSONField("Координаты", default=dict, blank=True)
    order = models.IntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Country(models.Model):
    """Страна с индексами из внешних источников"""

    SANCTION_LEVELS = [
        ("none", "Нет"),
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
        ("critical", "Критический"),
    ]

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="countries",
        verbose_name="Регион",
    )
    iso2 = models.CharField("ISO-2", max_length=2, unique=True)
    iso3 = models.CharField("ISO-3", max_length=3, unique=True)
    name_ru = models.CharField("Название (RU)", max_length=200)
    name_en = models.CharField("Название (EN)", max_length=200)

    # Кэшированные индексы из внешних источников
    wb_stability_index = models.FloatField(
        "World Bank Stability Index", null=True, blank=True
    )
    ti_cpi_score = models.FloatField(
        "Transparency Int. CPI", null=True, blank=True
    )
    imf_gdp_growth = models.FloatField(
        "IMF GDP Growth %", null=True, blank=True
    )
    sanction_risk_level = models.CharField(
        "Санкционный риск",
        max_length=20,
        choices=SANCTION_LEVELS,
        default="none",
    )
    last_updated = models.DateTimeField("Обновлено", auto_now=True, null=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
        ordering = ["name_ru"]

    def __str__(self):
        return f"{self.name_ru} ({self.iso2})"


class RouteNode(models.Model):
    """Узел маршрута: порт, КПП, терминал, ж/д станция"""

    NODE_TYPES = [
        ("port_sea", "Морской порт"),
        ("port_dry", "Сухой порт"),
        ("border", "Погранпереход"),
        ("terminal", "Терминал"),
        ("railway", "Ж/д станция"),
        ("airport", "Аэропорт"),
        ("hub", "Логистический хаб"),
    ]
    STATUS_CHOICES = [
        ("operational", "Работает"),
        ("limited", "Ограничено"),
        ("suspended", "Приостановлен"),
        ("closed", "Закрыт"),
    ]

    name = models.CharField("Название (RU)", max_length=300)
    name_en = models.CharField("Название (EN)", max_length=300, blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="route_nodes",
        verbose_name="Страна",
    )
    node_type = models.CharField("Тип узла", max_length=20, choices=NODE_TYPES)
    lat = models.DecimalField(
        "Широта", max_digits=9, decimal_places=6, null=True, blank=True
    )
    lng = models.DecimalField(
        "Долгота", max_digits=9, decimal_places=6, null=True, blank=True
    )
    capacity_teu_year = models.IntegerField(
        "Мощность (TEU/год)", null=True, blank=True
    )
    operator = models.CharField("Оператор", max_length=300, blank=True)
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="operational"
    )
    status_note = models.TextField("Примечание к статусу", blank=True)
    description = models.TextField("Описание", blank=True)
    is_emulated = models.BooleanField("Эмулированные данные", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Узел маршрута"
        verbose_name_plural = "Узлы маршрутов"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_node_type_display()})"


class TradeCorridor(models.Model):
    """Торговый коридор: ТМТМ, Северный коридор, INSTC, и т.д."""

    name = models.CharField("Название", max_length=300)
    code = models.CharField("Код", max_length=50, unique=True)
    description = models.TextField("Описание")
    nodes = models.ManyToManyField(
        RouteNode,
        through="CorridorNode",
        verbose_name="Узлы",
    )
    color = models.CharField("Цвет (hex)", max_length=7, default="#C6A46D")
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Торговый коридор"
        verbose_name_plural = "Торговые коридоры"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class CorridorNode(models.Model):
    """Связь узла с коридором (порядок, сегмент)"""

    SEGMENT_MODES = [
        ("rail", "Ж/д"),
        ("road", "Авто"),
        ("sea", "Море"),
        ("ferry", "Паром"),
        ("air", "Авиа"),
        ("river", "Река"),
    ]

    corridor = models.ForeignKey(
        TradeCorridor,
        on_delete=models.CASCADE,
        related_name="corridor_nodes",
        verbose_name="Коридор",
    )
    node = models.ForeignKey(
        RouteNode,
        on_delete=models.CASCADE,
        related_name="corridor_memberships",
        verbose_name="Узел",
    )
    order = models.IntegerField("Порядок", default=0)
    segment_distance_km = models.IntegerField(
        "Расстояние сегмента (км)", null=True, blank=True
    )
    segment_mode = models.CharField(
        "Тип транспорта", max_length=10, choices=SEGMENT_MODES, blank=True
    )

    class Meta:
        verbose_name = "Узел коридора"
        verbose_name_plural = "Узлы коридоров"
        ordering = ["corridor", "order"]
        unique_together = ["corridor", "node"]

    def __str__(self):
        return f"{self.corridor.code} → {self.node.name} (#{self.order})"
