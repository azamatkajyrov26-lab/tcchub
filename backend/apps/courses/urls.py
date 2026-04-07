from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CourseViewSet, EnrollmentViewSet, SectionViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("courses", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [
    path(
        "courses/<slug:course_slug>/sections/",
        SectionViewSet.as_view({"get": "list", "post": "create"}),
        name="course-sections-list",
    ),
    path(
        "courses/<slug:course_slug>/sections/<int:pk>/",
        SectionViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="course-sections-detail",
    ),
    path("", include(router.urls)),
]
