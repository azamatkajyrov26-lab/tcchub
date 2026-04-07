from django.db import models


class HeroSection(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    background_image = models.ImageField(upload_to="landing/hero/", blank=True)
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Hero sections"

    def __str__(self):
        return self.title


class Metric(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class Partner(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="landing/partners/")
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    author_name = models.CharField(max_length=255)
    author_role = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    avatar = models.ImageField(upload_to="landing/testimonials/", blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.author_name} - {self.author_role}"


class Advantage(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Contact info"

    def __str__(self):
        return self.email or "Contact Info"


class ContentBlock(models.Model):
    """Flexible content block for the landing page.

    Admin can create / edit / hide / reorder / delete these blocks
    without touching templates or breaking the page layout.
    """

    BLOCK_TYPES = [
        ("hero", "Hero (большой заголовок)"),
        ("text", "Текст (заголовок + абзац)"),
        ("feature_grid", "Сетка преимуществ"),
        ("stats", "Метрики / цифры"),
        ("cta", "Call to action"),
        ("quote", "Цитата"),
        ("image_text", "Картинка + текст"),
        ("divider", "Разделитель"),
        ("custom_html", "HTML (для сложных блоков)"),
    ]

    # Blocks whose content is too complex for inline form editing.
    # Admin can still hide/reorder/delete them, but edit is disabled.
    NON_EDITABLE_TYPES = {"custom_html"}

    block_type = models.CharField(max_length=32, choices=BLOCK_TYPES)
    eyebrow = models.CharField(max_length=120, blank=True,
                               help_text="Маленький надзаголовок (gold caps)")
    heading = models.CharField(max_length=255, blank=True)
    subheading = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True, help_text="Основной текст. Поддерживает переносы строк.")
    cta_label = models.CharField(max_length=80, blank=True)
    cta_url = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to="landing/blocks/", blank=True, null=True)
    data = models.JSONField(default=dict, blank=True,
                            help_text="Структурированные данные для feature_grid / stats и т.п.")
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"[{self.get_block_type_display()}] {self.heading or self.eyebrow or f'#{self.pk}'}"

    @property
    def is_editable(self):
        return self.block_type not in self.NON_EDITABLE_TYPES
