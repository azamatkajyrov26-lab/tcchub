from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DataSourceViewSet,
    NewsItemViewSet,
    SanctionEntryViewSet,
    SyncLogViewSet,
    TradeFlowViewSet,
)

router = DefaultRouter()
router.register("sources", DataSourceViewSet)
router.register("sync-logs", SyncLogViewSet)
router.register("sanctions", SanctionEntryViewSet)
router.register("trade-flows", TradeFlowViewSet)
router.register("news", NewsItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
