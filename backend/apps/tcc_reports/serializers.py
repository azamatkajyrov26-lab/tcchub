from rest_framework import serializers

from apps.tcc_reports.models import Report, ReportSection, ReportTemplate


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = ["id", "name", "code", "description", "sections_config", "is_active"]


class ReportSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSection
        fields = [
            "id",
            "order",
            "section_type",
            "title",
            "content",
            "data_config",
            "analyst_notes",
        ]


class ReportListSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    author = serializers.CharField(source="created_by.get_full_name", read_only=True)
    section_count = serializers.IntegerField(source="sections.count", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "template",
            "template_name",
            "status",
            "author",
            "is_free_preview",
            "price_usd",
            "views_count",
            "published_at",
            "created_at",
            "section_count",
            "cover_image",
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    author = serializers.CharField(source="created_by.get_full_name", read_only=True)
    sections = ReportSectionSerializer(many=True, read_only=True)
    corridor_names = serializers.SerializerMethodField()
    country_names = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "template",
            "template_name",
            "status",
            "author",
            "created_by",
            "reviewed_by",
            "published_by",
            "created_at",
            "updated_at",
            "published_at",
            "valid_until",
            "executive_summary",
            "key_findings",
            "recommendations",
            "is_free_preview",
            "preview_text",
            "price_usd",
            "pdf_file",
            "cover_image",
            "views_count",
            "downloads_count",
            "sections",
            "corridor_names",
            "country_names",
        ]

    def get_corridor_names(self, obj):
        return [{"id": c.id, "code": c.code, "name": c.name} for c in obj.corridors.all()]

    def get_country_names(self, obj):
        return [{"id": c.id, "iso2": c.iso2, "name": c.name_ru} for c in obj.countries.all()]


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "title",
            "subtitle",
            "template",
            "executive_summary",
            "key_findings",
            "recommendations",
            "is_free_preview",
            "preview_text",
            "price_usd",
            "corridors",
            "countries",
        ]


class ReportSectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSection
        fields = [
            "report",
            "order",
            "section_type",
            "title",
            "content",
            "data_config",
            "analyst_notes",
        ]
