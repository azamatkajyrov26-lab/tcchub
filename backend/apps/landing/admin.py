from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Advantage,
    ContactInfo,
    ContentBlock,
    HeroSection,
    Metric,
    Page,
    PageSection,
    Partner,
    SiteItem,
    Testimonial,
)


# ═══════════════════════════════════════════════════════════════
# CMS CORE — Page + PageSection
# ═══════════════════════════════════════════════════════════════

class PageSectionInline(TabularInline):
    model = PageSection
    extra = 0
    fields = ["is_visible", "order", "block_type", "section_key", "heading"]
    ordering = ["order", "id"]
    show_change_link = True
    classes = ["collapse"]


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ["title", "slug", "is_published", "updated_at"]
    list_filter = ["is_published"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageSectionInline]
    fieldsets = (
        ("Основное", {"fields": ("title", "slug", "is_published")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )


@admin.register(PageSection)
class PageSectionAdmin(ModelAdmin):
    list_display = ["page", "order", "block_type", "heading", "is_visible"]
    list_filter = ["page", "block_type", "is_visible"]
    list_editable = ["order", "is_visible"]
    search_fields = ["heading", "eyebrow", "body", "section_key"]
    autocomplete_fields = ["page"]
    fieldsets = (
        ("Привязка", {"fields": ("page", "block_type", "section_key", "order", "is_visible")}),
        ("Текст", {"fields": ("eyebrow", "heading", "subheading", "body")}),
        ("CTA и медиа", {"fields": ("cta_label", "cta_url", "image")}),
        ("Структурированные данные (JSON)", {"fields": ("data",)}),
    )


# ═══════════════════════════════════════════════════════════════
# Legacy CMS (кратко, для обратной совместимости)
# ═══════════════════════════════════════════════════════════════

@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ["block_type", "heading", "order", "is_visible"]
    list_filter = ["block_type", "is_visible"]
    list_editable = ["order", "is_visible"]
    search_fields = ["heading", "eyebrow", "body"]


@admin.register(HeroSection)
class HeroSectionAdmin(ModelAdmin):
    list_display = ["title", "is_active"]
    list_filter = ["is_active"]


@admin.register(Metric)
class MetricAdmin(ModelAdmin):
    list_display = ["label", "value", "description", "order"]
    list_editable = ["order"]


@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    list_display = ["name", "url", "order"]
    list_editable = ["order"]
    search_fields = ["name"]


@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display = ["author_name", "author_role", "order"]
    list_editable = ["order"]


@admin.register(Advantage)
class AdvantageAdmin(ModelAdmin):
    list_display = ["title", "icon", "order"]
    list_editable = ["order"]


@admin.register(ContactInfo)
class ContactInfoAdmin(ModelAdmin):
    list_display = ["email", "phone", "whatsapp", "address"]


@admin.register(SiteItem)
class SiteItemAdmin(ModelAdmin):
    list_display = ["title", "category", "subcategory", "order", "is_published"]
    list_filter = ["category", "subcategory", "is_published"]
    list_editable = ["order", "is_published"]
    search_fields = ["title", "subtitle", "description"]
    fieldsets = (
        ("Основное", {"fields": ("category", "subcategory", "order", "is_published")}),
        ("Контент", {"fields": ("title", "subtitle", "description")}),
        ("Изображение", {"fields": ("image", "image_url")}),
        ("Ссылка", {"fields": ("url",)}),
        ("Доп. данные (JSON)", {"fields": ("data",)}),
    )
