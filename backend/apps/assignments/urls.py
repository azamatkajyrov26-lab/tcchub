from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AssignmentViewSet, SubmissionFileViewSet, SubmissionViewSet

router = DefaultRouter()
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", SubmissionViewSet, basename="submission")
router.register("submission-files", SubmissionFileViewSet, basename="submission-file")

urlpatterns = [
    path("", include(router.urls)),
]
