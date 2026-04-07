from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("risk-factors", views.RiskFactorViewSet, basename="risk-factors")
router.register("scores", views.RouteScoreViewSet, basename="scores")
router.register("scenarios", views.ScenarioViewSet, basename="scenarios")

urlpatterns = [
    path("", include(router.urls)),
]
