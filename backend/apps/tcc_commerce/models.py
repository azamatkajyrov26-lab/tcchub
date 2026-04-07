from django.conf import settings
from django.db import models


class Product(models.Model):
    """Продукт для продажи: отдельный отчёт или подписка"""

    PRODUCT_TYPES = [
        ("single_report", "Отдельный отчёт"),
        ("subscription_monthly", "Подписка месяц"),
        ("subscription_annual", "Подписка год"),
        ("data_feed", "Дата-фид"),
        ("custom", "Кастомный"),
    ]

    product_type = models.CharField(
        "Тип продукта", max_length=30, choices=PRODUCT_TYPES
    )
    name = models.CharField("Название", max_length=300)
    description = models.TextField("Описание")
    price_usd = models.DecimalField("Цена (USD)", max_digits=10, decimal_places=2)
    report = models.ForeignKey(
        "tcc_reports.Report",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name="Отчёт",
    )
    included_report_templates = models.ManyToManyField(
        "tcc_reports.ReportTemplate",
        blank=True,
        verbose_name="Включённые шаблоны",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["price_usd"]

    def __str__(self):
        return f"{self.name} (${self.price_usd})"


class Order(models.Model):
    """Заказ пользователя"""

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("paid", "Оплачен"),
        ("cancelled", "Отменён"),
        ("refunded", "Возврат"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tcc_orders",
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Продукт",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    amount_usd = models.DecimalField("Сумма (USD)", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    paid_at = models.DateTimeField("Оплачен", null=True, blank=True)
    payment_ref = models.CharField("Ссылка на оплату", max_length=300, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.pk} — {self.user} — {self.get_status_display()}"


class ReportAccess(models.Model):
    """Права доступа пользователя к отчёту"""

    ACCESS_TYPES = [
        ("purchase", "Куплен"),
        ("subscription", "Подписка"),
        ("free", "Бесплатный"),
        ("demo", "Демо"),
        ("admin", "Админ"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_accesses",
        verbose_name="Пользователь",
    )
    report = models.ForeignKey(
        "tcc_reports.Report",
        on_delete=models.CASCADE,
        related_name="accesses",
        verbose_name="Отчёт",
    )
    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Заказ",
    )
    granted_at = models.DateTimeField("Выдан", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает", null=True, blank=True)
    access_type = models.CharField(
        "Тип доступа", max_length=20, choices=ACCESS_TYPES
    )

    class Meta:
        verbose_name = "Доступ к отчёту"
        verbose_name_plural = "Доступы к отчётам"
        unique_together = ["user", "report"]

    def __str__(self):
        return f"{self.user} → {self.report.title} ({self.get_access_type_display()})"
