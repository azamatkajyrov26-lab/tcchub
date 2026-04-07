from django.contrib import admin

from apps.tcc_commerce.models import Order, Product, ReportAccess


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "product_type", "price_usd", "is_active", "created_at"]
    list_filter = ["product_type", "is_active"]
    search_fields = ["name", "description"]
    filter_horizontal = ["included_report_templates"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "status", "amount_usd", "created_at", "paid_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "payment_ref"]
    readonly_fields = ["created_at"]


@admin.register(ReportAccess)
class ReportAccessAdmin(admin.ModelAdmin):
    list_display = ["user", "report", "access_type", "granted_at", "expires_at"]
    list_filter = ["access_type"]
    search_fields = ["user__email", "report__title"]
