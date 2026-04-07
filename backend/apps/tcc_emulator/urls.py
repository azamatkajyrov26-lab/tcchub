from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("sources", views.EmulatedDataSourceViewSet, basename="emulated-sources")
router.register("node-statuses", views.EmulatedNodeStatusViewSet, basename="node-statuses")

urlpatterns = [
    path("", include(router.urls)),
]
