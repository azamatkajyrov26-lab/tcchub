from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BadgeIssuanceViewSet, BadgeViewSet

router = DefaultRouter()
router.register("badges", BadgeViewSet, basename="badge")
router.register("issuances", BadgeIssuanceViewSet, basename="badge-issuance")

urlpatterns = [
    path("", include(router.urls)),
]
