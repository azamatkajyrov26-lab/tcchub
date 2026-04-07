from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Advantage, ContactInfo, HeroSection, Metric, Partner, Testimonial


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
