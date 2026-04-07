from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.tcc_commerce.models import Order, Product, ReportAccess
from apps.tcc_commerce.serializers import (
    OrderSerializer,
    ProductSerializer,
    ReportAccessSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["product_type"]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product")

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product")
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Продукт не найден"}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(
            user=request.user,
            product=product,
            amount_usd=product.price_usd,
            status="pending",
        )

        # Auto-complete for free products or demo
        if product.price_usd == 0:
            order.status = "paid"
            order.paid_at = timezone.now()
            order.save()
            # Grant access
            if product.report:
                ReportAccess.objects.get_or_create(
                    user=request.user,
                    report=product.report,
                    defaults={"order": order, "access_type": "free"},
                )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="simulate-payment")
    def simulate_payment(self, request, pk=None):
        """Эмуляция оплаты (для тестирования)"""
        order = self.get_object()
        if order.status != "pending":
            return Response({"error": "Заказ уже обработан"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = "paid"
        order.paid_at = timezone.now()
        order.payment_ref = f"SIM-{order.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        order.save()

        # Grant access
        if order.product.report:
            ReportAccess.objects.get_or_create(
                user=request.user,
                report=order.product.report,
                defaults={"order": order, "access_type": "purchase"},
            )

        return Response(OrderSerializer(order).data)


class MyReportAccessViewSet(viewsets.ReadOnlyModelViewSet):
    """Мои купленные отчёты"""

    serializer_class = ReportAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportAccess.objects.filter(user=self.request.user).select_related("report")
