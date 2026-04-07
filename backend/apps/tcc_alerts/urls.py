from rest_framework.routers import DefaultRouter

from .views import AlertViewSet, AlertSubscriptionViewSet

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alert")
router.register("subscriptions", AlertSubscriptionViewSet, basename="alert-subscription")

urlpatterns = router.urls
