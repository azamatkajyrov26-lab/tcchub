from django.conf import settings
from django.db import models


class ReportTemplate(models.Model):
    """Шаблон типа отчёта"""

    name = models.CharField("Название", max_length=300)
    code = models.CharField("Код", max_length=100, unique=True)
    description = models.TextField("Описание")
    sections_config = models.JSONField("Конфигурация секций", default=list, blank=True)
    html_template = models.CharField(
        "HTML шаблон", max_length=300, default="reports/pdf/base_report.html"
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Шаблон отчёта"
        verbose_name_plural = "Шаблоны отчётов"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Report(models.Model):
    """Отчёт — создаётся аналитиком, продаётся клиентам"""

    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("in_review", "На проверке"),
        ("approved", "Утверждён"),
        ("published", "Опубликован"),
        ("archived", "Архив"),
    ]

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="Шаблон",
    )
    title = models.CharField("Заголовок", max_length=500)
    subtitle = models.CharField("Подзаголовок", max_length=500, blank=True)
    slug = models.SlugField("Slug", max_length=200, unique=True, blank=True)

    corridors = models.ManyToManyField(
        "tcc_core.TradeCorridor", blank=True, verbose_name="Коридоры"
    )
    countries = models.ManyToManyField(
        "tcc_core.Country", blank=True, verbose_name="Страны"
    )

    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="draft"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_reports",
        verbose_name="Автор",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reports",
        verbose_name="Проверил",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_reports",
        verbose_name="Опубликовал",
    )

    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    published_at = models.DateTimeField("Опубликован", null=True, blank=True)
    valid_until = models.DateField("Действителен до", null=True, blank=True)

    executive_summary = models.TextField("Executive Summary", blank=True)
    key_findings = models.JSONField("Ключевые выводы", default=list, blank=True)
    recommendations = models.JSONField("Рекомендации", default=list, blank=True)

    is_free_preview = models.BooleanField("Бесплатный превью", default=False)
    preview_text = models.TextField("Текст превью", blank=True)
    price_usd = models.DecimalField(
        "Цена (USD)", max_digits=10, decimal_places=2, default=0
    )

    pdf_file = models.FileField("PDF файл", upload_to="reports/pdf/", blank=True)
    cover_image = models.ImageField("Обложка", upload_to="reports/covers/", blank=True)

    views_count = models.IntegerField("Просмотры", default=0)
    downloads_count = models.IntegerField("Скачивания", default=0)

    class Meta:
        verbose_name = "Отчёт"
        verbose_name_plural = "Отчёты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.title, allow_unicode=True)[:180]
            self.slug = base or f"report-{self.pk or 'new'}"
            # Ensure uniqueness
            if Report.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                import uuid
                self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)


class ReportSection(models.Model):
    """Секция внутри отчёта"""

    SECTION_TYPES = [
        ("text", "Текст"),
        ("risk_table", "Таблица рисков"),
        ("route_score", "Скор маршрута"),
        ("scenario_comparison", "Сравнение сценариев"),
        ("trade_flow_chart", "График торговли"),
        ("sanction_check", "Санкционная проверка"),
        ("country_profile", "Профиль страны"),
        ("map", "Карта"),
        ("custom_chart", "Произвольный график"),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Отчёт",
    )
    order = models.IntegerField("Порядок", default=0)
    section_type = models.CharField(
        "Тип секции", max_length=30, choices=SECTION_TYPES
    )
    title = models.CharField("Заголовок", max_length=300, blank=True)
    content = models.TextField("Содержание", blank=True)
    data_config = models.JSONField(
        "Конфигурация данных", default=dict, blank=True
    )
    analyst_notes = models.TextField("Заметки аналитика", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Секция отчёта"
        verbose_name_plural = "Секции отчётов"
        ordering = ["report", "order"]

    def __str__(self):
        return f"{self.report.title} → {self.title or self.get_section_type_display()} (#{self.order})"
