from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DiscussionViewSet, ForumViewSet, PostViewSet

router = DefaultRouter()
router.register("forums", ForumViewSet, basename="forum")
router.register("discussions", DiscussionViewSet, basename="discussion")
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
]
