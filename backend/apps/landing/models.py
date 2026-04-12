from django.db import models


# ═══════════════════════════════════════════════════════════════
# CMS CORE — Page + PageSection
# ═══════════════════════════════════════════════════════════════

class Page(models.Model):
    """Публичная страница сайта. Каждая страница имеет набор секций (блоков),
    которые можно редактировать, скрывать, менять местами через админку.
    """
    slug = models.SlugField(unique=True, max_length=100,
                            help_text="Технический идентификатор: landing, about, solutions…")
    title = models.CharField(max_length=255, help_text="Заголовок для админки")
    meta_title = models.CharField(max_length=200, blank=True,
                                  help_text="<title> в HTML. Если пусто — берётся title")
    meta_description = models.TextField(blank=True, max_length=300,
                                        help_text="<meta description> для SEO")
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Страница сайта"
        verbose_name_plural = "Страницы сайта"
        ordering = ["slug"]

    def __str__(self):
        return f"{self.title} (/{self.slug})"


class PageSection(models.Model):
    """Блок/секция на странице. Можно добавлять/удалять/редактировать/скрывать
    без правки шаблонов. Шаблон итерирует по секциям и рендерит их по block_type.
    """

    BLOCK_TYPES = [
        ("hero", "Hero — большой заголовок"),
        ("text", "Текст — заголовок + абзац"),
        ("text_image", "Текст + изображение"),
        ("feature_grid", "Сетка преимуществ / features"),
        ("stats", "Метрики / цифры"),
        ("cta", "Call to action"),
        ("quote", "Цитата"),
        ("bento", "Editorial bento (карточки)"),
        ("partners_grid", "Логотипы партнёров"),
        ("custom_html", "Сырой HTML"),
        ("divider", "Разделитель"),
    ]

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="sections")
    section_key = models.SlugField(max_length=80, blank=True,
                                   help_text="Опциональный якорь/id для секции")
    block_type = models.CharField(max_length=32, choices=BLOCK_TYPES, default="text")

    eyebrow = models.CharField(max_length=120, blank=True,
                               help_text="Маленький надзаголовок (gold caps)")
    heading = models.CharField(max_length=255, blank=True)
    subheading = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True,
                            help_text="Основной текст. Поддерживает HTML и переносы строк.")
    cta_label = models.CharField(max_length=80, blank=True)
    cta_url = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to="cms/sections/", blank=True, null=True)

    data = models.JSONField(default=dict, blank=True,
                            help_text="Структурированные данные: items для feature_grid, "
                                      "цифры для stats, и т.д. Пример: "
                                      '[{"label":"Grueopotok","value":"4.5 млн т"}]')

    order = models.PositiveIntegerField(default=0, db_index=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Блок страницы"
        verbose_name_plural = "Блоки страниц"
        ordering = ["page", "order", "id"]

    def __str__(self):
        label = self.heading or self.eyebrow or self.section_key or f"#{self.pk}"
        return f"{self.page.slug} · {self.get_block_type_display()} · {label}"


# ═══════════════════════════════════════════════════════════════
# Legacy / specific models (backwards compatible)
# ═══════════════════════════════════════════════════════════════

class HeroSection(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    background_image = models.ImageField(upload_to="landing/hero/", blank=True)
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Hero блок (главная)"
        verbose_name_plural = "Hero блоки (главная)"

    def __str__(self):
        return self.title


class Metric(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Метрика / цифра"
        verbose_name_plural = "Метрики / цифры"
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class Partner(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="landing/partners/")
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Партнёр"
        verbose_name_plural = "Партнёры"
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
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["order"]

    def __str__(self):
        return f"{self.author_name} - {self.author_role}"


class Advantage(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Преимущество"
        verbose_name_plural = "Преимущества"
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
        verbose_name = "Контактная информация"
        verbose_name_plural = "Контактная информация"

    def __str__(self):
        return self.email or "Contact Info"


class SiteNews(models.Model):
    """Редакционные новости/материалы для блоков на главной и /press/.
    Заполняются админом через кабинет CMS (/dashboard/cms/news/).
    """

    TYPE_CHOICES = [
        ("статья", "Статья"),
        ("интервью", "Интервью"),
        ("исследование", "Исследование"),
        ("видео", "Видео"),
        ("мероприятие", "Мероприятие"),
        ("новость", "Новость"),
    ]

    title = models.CharField("Заголовок", max_length=300)
    kind = models.CharField("Тип", max_length=32, choices=TYPE_CHOICES, default="новость")
    excerpt = models.TextField("Краткое описание", max_length=600, blank=True)
    body = models.TextField("Полный текст (HTML)", blank=True)
    cover = models.ImageField("Обложка", upload_to="news/", blank=True, null=True)
    cover_url = models.URLField("URL внешней обложки", max_length=1000, blank=True,
                                help_text="Используется если нет загруженной обложки")
    external_url = models.URLField("Внешняя ссылка (опц.)", max_length=1000, blank=True)
    published_at = models.DateField("Дата публикации")
    is_published = models.BooleanField("Опубликовано", default=True)
    show_on_landing = models.BooleanField("Показывать на главной", default=False,
                                          help_text="Один из плавающих блоков hero")
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Новость сайта"
        verbose_name_plural = "Новости сайта"
        ordering = ["-published_at", "order", "-id"]

    def __str__(self):
        return self.title[:80]

    @property
    def cover_src(self):
        if self.cover:
            return self.cover.url
        return self.cover_url or ""


class SiteItem(models.Model):
    """Универсальная модель для всех списочных материалов сайта:
    статьи аналитики, партнёры, проекты, программы обучения, отчёты и т.д.
    Одна модель + одна админка + параметризация по category.
    """

    CATEGORY_CHOICES = [
        ("article", "Статья аналитики"),
        ("partner", "Партнёр"),
        ("project", "Проект"),
        ("program", "Программа обучения"),
        ("report", "Отчёт"),
        ("team", "Член команды"),
        ("expert", "Эксперт"),
        ("solution", "Направление / решение"),
    ]

    category = models.CharField("Категория", max_length=32, choices=CATEGORY_CHOICES, db_index=True)
    subcategory = models.CharField("Подкатегория", max_length=80, blank=True,
                                   help_text="Напр. 'international'/'education' для партнёров, "
                                             "'middle_corridor'/'research' для проектов")
    slug = models.SlugField("Slug", max_length=200, blank=True)
    title = models.CharField("Заголовок", max_length=300)
    subtitle = models.CharField("Подзаголовок", max_length=300, blank=True)
    description = models.TextField("Описание", max_length=1500, blank=True)
    body = models.TextField("Полный текст (HTML)", blank=True)
    image = models.ImageField("Изображение/лого", upload_to="site_items/", blank=True, null=True)
    image_url = models.URLField("URL изображения", max_length=1000, blank=True)
    link_url = models.URLField("Ссылка", max_length=1000, blank=True)
    tag = models.CharField("Тег/бейдж", max_length=80, blank=True)
    status = models.CharField("Статус", max_length=40, blank=True,
                              help_text="Напр. 'активный'/'в разработке'")
    data = models.JSONField("Доп. данные", default=dict, blank=True,
                            help_text="Метрики, доп. поля: {'metrics': ['4.5 млн т','EUR 18.5 млрд']}")
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)
    is_published = models.BooleanField("Опубликовано", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Материал сайта"
        verbose_name_plural = "Материалы сайта"
        ordering = ["category", "order", "-id"]
        indexes = [models.Index(fields=["category", "subcategory", "order"])]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title[:60]}"

    @property
    def image_src(self):
        if self.image:
            return self.image.url
        return self.image_url or ""


class ContentBlock(models.Model):
    """Legacy flexible content block (оставлен для обратной совместимости)."""

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

    NON_EDITABLE_TYPES = {"custom_html"}

    block_type = models.CharField(max_length=32, choices=BLOCK_TYPES)
    eyebrow = models.CharField(max_length=120, blank=True)
    heading = models.CharField(max_length=255, blank=True)
    subheading = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)
    cta_label = models.CharField(max_length=80, blank=True)
    cta_url = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to="landing/blocks/", blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Legacy блок главной"
        verbose_name_plural = "Legacy блоки главной"
        ordering = ["order", "id"]

    def __str__(self):
        return f"[{self.get_block_type_display()}] {self.heading or self.eyebrow or f'#{self.pk}'}"

    @property
    def is_editable(self):
        return self.block_type not in self.NON_EDITABLE_TYPES


class ContactSubmission(models.Model):
    """Заявки с контактной формы сайта."""
    name = models.CharField("Имя", max_length=200)
    phone = models.CharField("Телефон", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Сообщение", blank=True)
    source = models.CharField("Источник", max_length=40, default="contacts",
                              help_text="contacts / landing / bot")
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.created_at:%d.%m.%Y %H:%M}"
