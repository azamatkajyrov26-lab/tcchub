from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseReportViewSet, LoginLogViewSet, UserActivityViewSet

router = DefaultRouter()
router.register("activities", UserActivityViewSet, basename="user-activity")
router.register("reports", CourseReportViewSet, basename="course-report")
router.register("logins", LoginLogViewSet, basename="login-log")

urlpatterns = [
    path("", include(router.urls)),
]
