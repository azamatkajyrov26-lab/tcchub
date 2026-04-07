from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CountryViewSet, RegionViewSet, RouteNodeViewSet, TradeCorridorViewSet

router = DefaultRouter()
router.register("regions", RegionViewSet)
router.register("countries", CountryViewSet)
router.register("nodes", RouteNodeViewSet)
router.register("corridors", TradeCorridorViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
