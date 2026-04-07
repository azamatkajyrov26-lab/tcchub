from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("templates", views.ReportTemplateViewSet, basename="report-templates")
router.register("public", views.PublicReportViewSet, basename="public-reports")
router.register("workspace", views.WorkspaceReportViewSet, basename="workspace-reports")
router.register("sections", views.ReportSectionViewSet, basename="report-sections")

urlpatterns = [
    path("", include(router.urls)),
]
