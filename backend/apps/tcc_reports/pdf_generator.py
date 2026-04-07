"""
PDF generation for TCC reports using WeasyPrint.
"""

import logging

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.tcc_reports.models import Report

logger = logging.getLogger(__name__)


def generate_report_pdf(report_id: int) -> str:
    """Генерирует PDF и сохраняет в report.pdf_file"""
    report = Report.objects.prefetch_related(
        "sections", "corridors", "countries"
    ).select_related("template", "created_by").get(id=report_id)

    # Collect route scores for corridors
    scores_data = {}
    for corridor in report.corridors.all():
        from apps.tcc_intelligence.models import RouteScore

        latest = (
            RouteScore.objects.filter(corridor=corridor)
            .order_by("-calculated_at")
            .first()
        )
        if latest:
            scores_data[corridor.code] = {
                "total": latest.score_total,
                "risk_level": latest.risk_level,
                "sanctions": latest.score_sanctions,
                "geopolitical": latest.score_geopolitical,
                "infrastructure": latest.score_infrastructure,
                "regulatory": latest.score_regulatory,
                "financial": latest.score_financial,
            }

    # Collect risk factors
    risk_factors = []
    for corridor in report.corridors.all():
        from apps.tcc_intelligence.models import RiskFactor

        factors = RiskFactor.objects.filter(
            corridor=corridor, is_active=True
        ).order_by("-impact_score")[:10]
        risk_factors.extend(factors)

    # Collect scenarios
    scenarios = []
    for corridor in report.corridors.all():
        from apps.tcc_intelligence.models import Scenario

        corridor_scenarios = Scenario.objects.filter(corridor=corridor)
        scenarios.extend(corridor_scenarios)

    template_name = report.template.html_template
    html_content = render_to_string(
        template_name,
        {
            "report": report,
            "sections": report.sections.order_by("order"),
            "generated_at": timezone.now(),
            "scores_data": scores_data,
            "risk_factors": risk_factors,
            "scenarios": scenarios,
        },
    )

    pdf_bytes = HTML(string=html_content).write_pdf()

    filename = f"tcc_report_{report.id}_{timezone.now().strftime('%Y%m%d')}.pdf"
    report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    report.save(update_fields=["pdf_file"])

    logger.info("Generated PDF for report #%d: %s", report.id, filename)
    return report.pdf_file.url
