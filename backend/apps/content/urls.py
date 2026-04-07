from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityCompletionViewSet,
    ActivityViewSet,
    FolderFileViewSet,
    FolderViewSet,
    ResourceViewSet,
)

router = DefaultRouter()
router.register("activities", ActivityViewSet, basename="activity")
router.register("resources", ResourceViewSet, basename="resource")
router.register("folders", FolderViewSet, basename="folder")
router.register("folder-files", FolderFileViewSet, basename="folder-file")
router.register("completions", ActivityCompletionViewSet, basename="activity-completion")

urlpatterns = [
    path("", include(router.urls)),
]
