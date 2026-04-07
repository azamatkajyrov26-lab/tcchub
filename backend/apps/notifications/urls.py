from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationPreferenceViewSet, NotificationTypeViewSet, NotificationViewSet

router = DefaultRouter()
router.register("types", NotificationTypeViewSet, basename="notification-type")
router.register("preferences", NotificationPreferenceViewSet, basename="notification-preference")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]
