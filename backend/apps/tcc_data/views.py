from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes as perm_dec
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


@api_view(["GET"])
@perm_dec([AllowAny])
def live_news_feed(request):
    """
    Public endpoint for the homepage Live News slider & Актуальная повестка.
    Returns latest news items grouped for frontend consumption.
    GET /api/v1/tcc/data/live-news/?limit=20
    """
    limit = min(int(request.query_params.get("limit", 20)), 50)

    items = (
        NewsItem.objects
        .select_related("source")
        .order_by("-published_at")[:limit]
    )

    results = []
    for item in items:
        # Determine tone based on content keywords
        title_lower = (item.title or "").lower()
        content_lower = (item.content or "").lower()
        combined = f"{title_lower} {content_lower}"

        if any(w in combined for w in ["risk", "delay", "crisis", "decline", "drop",
                                        "санкц", "задерж", "ограничен", "risk", "alert"]):
            tone = "alert"
        elif any(w in combined for w in ["growth", "record", "launch", "open", "deal",
                                          "рост", "рекорд", "запуск", "открыт", "соглаш"]):
            tone = "ok"
        else:
            tone = "info"

        # Time ago calculation
        if item.published_at:
            delta = timezone.now() - item.published_at
            hours = int(delta.total_seconds() / 3600)
            if hours < 1:
                time_ago = f"{int(delta.total_seconds() / 60)} мин назад"
            elif hours < 24:
                time_ago = f"{hours} ч назад"
            else:
                days = hours // 24
                time_ago = f"{days} дн назад"
        else:
            time_ago = ""

        results.append({
            "id": item.id,
            "source": item.source.name if item.source else "",
            "source_code": item.source.code if item.source else "",
            "title": item.title,
            "content": (item.content or "")[:300],
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "time_ago": time_ago,
            "tone": tone,
            "language": item.language,
        })

    return Response({"count": len(results), "results": results})
