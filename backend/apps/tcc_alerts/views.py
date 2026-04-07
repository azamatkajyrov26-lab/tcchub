from django.db.models import Case, When, Value, IntegerField
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Alert, AlertSubscription
from .serializers import AlertSerializer, AlertSubscriptionSerializer


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related(
        "corridor", "country", "node", "related_score"
    )
    serializer_class = AlertSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["alert_type", "severity", "is_resolved", "corridor"]

    @action(detail=False, methods=["get"])
    def active(self, request):
        severity_order = Case(
            When(severity="critical", then=Value(0)),
            When(severity="warning", then=Value(1)),
            When(severity="info", then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
        alerts = (
            self.get_queryset()
            .filter(is_resolved=False)
            .annotate(severity_order=severity_order)
            .order_by("severity_order", "-created_at")
        )
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


class AlertSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AlertSubscription.objects.filter(
            user=self.request.user
        ).select_related("corridor")
