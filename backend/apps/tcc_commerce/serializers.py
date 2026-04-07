from rest_framework import serializers

from apps.tcc_commerce.models import Order, Product, ReportAccess


class ProductSerializer(serializers.ModelSerializer):
    report_title = serializers.CharField(source="report.title", read_only=True, default="")

    class Meta:
        model = Product
        fields = [
            "id",
            "product_type",
            "name",
            "description",
            "price_usd",
            "report",
            "report_title",
            "is_active",
        ]


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "product",
            "product_name",
            "status",
            "amount_usd",
            "created_at",
            "paid_at",
            "payment_ref",
        ]


class ReportAccessSerializer(serializers.ModelSerializer):
    report_title = serializers.CharField(source="report.title", read_only=True)

    class Meta:
        model = ReportAccess
        fields = [
            "id",
            "report",
            "report_title",
            "access_type",
            "granted_at",
            "expires_at",
        ]
