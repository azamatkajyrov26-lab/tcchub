from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GradeCategoryViewSet, GradeItemViewSet, GradeViewSet

router = DefaultRouter()
router.register("categories", GradeCategoryViewSet, basename="grade-category")
router.register("items", GradeItemViewSet, basename="grade-item")
router.register("grades", GradeViewSet, basename="grade")

urlpatterns = [
    path("", include(router.urls)),
]
