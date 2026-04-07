from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from apps.tcc_intelligence.models import RiskFactor, RouteScore, Scenario
from apps.tcc_intelligence.scoring import calculate_corridor_risk
from apps.tcc_intelligence.serializers import (
    RiskFactorSerializer,
    RouteScoreSerializer,
    ScenarioSerializer,
)


class RiskFactorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RiskFactor.objects.select_related("corridor", "country", "node").filter(
        is_active=True
    )
    serializer_class = RiskFactorSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["risk_category", "corridor", "country", "source_type"]
    search_fields = ["title", "description"]


class RouteScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RouteScore.objects.select_related("corridor")
    serializer_class = RouteScoreSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["corridor", "risk_level"]

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        """Последний скор для каждого коридора"""
        from apps.tcc_core.models import TradeCorridor

        corridors = TradeCorridor.objects.filter(is_active=True)
        results = []
        for corridor in corridors:
            score = (
                RouteScore.objects.filter(corridor=corridor)
                .order_by("-calculated_at")
                .first()
            )
            if score:
                results.append(RouteScoreSerializer(score).data)
        return Response(results)

    @action(detail=False, methods=["post"], url_path="recalculate", permission_classes=[IsAdminUser])
    def recalculate(self, request):
        """Пересчитать скоры для всех коридоров"""
        from apps.tcc_core.models import TradeCorridor

        corridors = TradeCorridor.objects.filter(is_active=True)
        results = []
        for corridor in corridors:
            score = calculate_corridor_risk(corridor.id)
            results.append(RouteScoreSerializer(score).data)
        return Response(results)


class ScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scenario.objects.select_related("corridor")
    serializer_class = ScenarioSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["corridor", "is_recommended"]
