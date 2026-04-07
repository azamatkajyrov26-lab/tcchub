from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContactRequestViewSet, ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")
router.register("messages", MessageViewSet, basename="message")
router.register("contacts", ContactRequestViewSet, basename="contact-request")

urlpatterns = [
    path("", include(router.urls)),
]
