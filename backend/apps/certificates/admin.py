from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CertificateTemplate, IssuedCertificate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(ModelAdmin):
    list_display = ["name", "course", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(IssuedCertificate)
class IssuedCertificateAdmin(ModelAdmin):
    list_display = ["certificate_number", "user", "course", "issued_at"]
    search_fields = ["certificate_number", "user__email"]
    readonly_fields = ["certificate_number", "issued_at"]
