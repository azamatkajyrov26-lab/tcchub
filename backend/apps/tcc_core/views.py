from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Country, Region, RouteNode, TradeCorridor
from .serializers import (
    CountrySerializer,
    RegionSerializer,
    RouteNodeSerializer,
    TradeCorridorDetailSerializer,
    TradeCorridorListSerializer,
)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.select_related("parent")
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["region_type", "parent"]
    search_fields = ["name", "name_en"]


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.select_related("region")
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["sanction_risk_level", "region"]
    search_fields = ["name_ru", "name_en", "iso2", "iso3"]


class RouteNodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RouteNode.objects.select_related("country")
    serializer_class = RouteNodeSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["node_type", "status", "country", "is_emulated"]
    search_fields = ["name", "name_en", "operator"]


class TradeCorridorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradeCorridor.objects.prefetch_related(
        "corridor_nodes__node__country"
    )
    permission_classes = [AllowAny]
    filterset_fields = ["is_active"]
    search_fields = ["name", "code"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TradeCorridorDetailSerializer
        return TradeCorridorListSerializer
