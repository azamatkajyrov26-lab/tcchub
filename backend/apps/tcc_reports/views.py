from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.tcc_reports.models import Report, ReportSection, ReportTemplate
from apps.tcc_reports.serializers import (
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    ReportSectionCreateSerializer,
    ReportSectionSerializer,
    ReportTemplateSerializer,
)


class ReportTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportTemplate.objects.filter(is_active=True)
    serializer_class = ReportTemplateSerializer
    permission_classes = [AllowAny]


class PublicReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Публичные отчёты — только опубликованные"""

    queryset = (
        Report.objects.filter(status="published")
        .select_related("template", "created_by")
        .prefetch_related("corridors", "countries")
    )
    permission_classes = [AllowAny]
    filterset_fields = ["template", "is_free_preview"]
    search_fields = ["title", "subtitle", "executive_summary"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReportDetailSerializer
        return ReportListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views
        Report.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class WorkspaceReportViewSet(viewsets.ModelViewSet):
    """Workspace — CRUD отчётов для аналитиков"""

    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "template"]
    search_fields = ["title", "subtitle"]

    def get_queryset(self):
        return (
            Report.objects.filter(created_by=self.request.user)
            .select_related("template", "created_by")
            .prefetch_related("sections", "corridors", "countries")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ReportCreateSerializer
        if self.action == "retrieve":
            return ReportDetailSerializer
        return ReportListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="submit-review")
    def submit_review(self, request, pk=None):
        """Отправить на проверку: draft → in_review"""
        report = self.get_object()
        if report.status != "draft":
            return Response(
                {"error": "Только черновик можно отправить на проверку"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = "in_review"
        report.save(update_fields=["status", "updated_at"])
        return Response({"status": "in_review"})

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Утвердить: in_review → approved"""
        report = self.get_object()
        if report.status != "in_review":
            return Response(
                {"error": "Только отчёт на проверке можно утвердить"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = "approved"
        report.reviewed_by = request.user
        report.save(update_fields=["status", "reviewed_by", "updated_at"])
        return Response({"status": "approved"})

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """Опубликовать: approved → published"""
        report = self.get_object()
        if report.status != "approved":
            return Response(
                {"error": "Только утверждённый отчёт можно опубликовать"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = "published"
        report.published_by = request.user
        report.published_at = timezone.now()
        report.save(update_fields=["status", "published_by", "published_at", "updated_at"])

        # Generate PDF async
        from apps.tcc_reports.tasks import generate_report_pdf_task

        generate_report_pdf_task.delay(report.id)

        return Response({"status": "published"})

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Архивировать"""
        report = self.get_object()
        report.status = "archived"
        report.save(update_fields=["status", "updated_at"])
        return Response({"status": "archived"})

    @action(detail=True, methods=["post"], url_path="generate-pdf")
    def generate_pdf(self, request, pk=None):
        """Сгенерировать PDF вручную"""
        report = self.get_object()
        from apps.tcc_reports.tasks import generate_report_pdf_task

        generate_report_pdf_task.delay(report.id)
        return Response({"message": "PDF генерация запущена"})


class ReportSectionViewSet(viewsets.ModelViewSet):
    """CRUD секций отчёта"""

    serializer_class = ReportSectionCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportSection.objects.filter(
            report__created_by=self.request.user
        ).select_related("report")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ReportSectionSerializer
        return ReportSectionCreateSerializer
