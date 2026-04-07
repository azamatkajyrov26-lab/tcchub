from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import DataSource, NewsItem, SanctionEntry, SyncLog, TradeFlow
from .serializers import (
    DataSourceSerializer,
    NewsItemSerializer,
    SanctionEntrySerializer,
    SyncLogSerializer,
    TradeFlowSerializer,
)


class DataSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["source_type", "access_status", "is_active"]
    search_fields = ["name", "code"]


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SyncLog.objects.select_related("source")
    serializer_class = SyncLogSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["status", "source"]


class SanctionEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SanctionEntry.objects.select_related("source")
    serializer_class = SanctionEntrySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["entity_type", "source", "is_active"]
    search_fields = ["name_primary"]

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """Поиск по санкционным спискам по имени/псевдониму"""
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response(
                {"error": "Минимум 2 символа для поиска"}, status=400
            )

        entries = SanctionEntry.objects.filter(
            Q(name_primary__icontains=q) | Q(name_aliases__icontains=q),
            is_active=True,
        ).select_related("source")[:50]

        serializer = SanctionEntrySerializer(entries, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})


class TradeFlowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradeFlow.objects.select_related("reporter_country", "partner_country", "source")
    serializer_class = TradeFlowSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["reporter_country", "partner_country", "year", "flow_type", "hs_code"]
    ordering_fields = ["value_usd", "year"]


class NewsItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsItem.objects.select_related("source")
    serializer_class = NewsItemSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["ai_processed", "ai_is_relevant", "language", "source"]
    search_fields = ["title", "content"]
    ordering_fields = ["published_at", "ai_severity"]
