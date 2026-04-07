"""
Django template views for the workspace (HTMX-powered report editor).
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.tcc_core.models import Country, TradeCorridor
from apps.tcc_data.models import NewsItem, SanctionEntry
from apps.tcc_intelligence.models import RiskFactor, RouteScore, Scenario
from apps.tcc_reports.models import Report, ReportSection, ReportTemplate


@login_required
def workspace_reports_list(request):
    reports = Report.objects.filter(created_by=request.user).select_related("template")
    current_status = request.GET.get("status", "")
    if current_status:
        reports = reports.filter(status=current_status)
    return render(request, "workspace/reports_list.html", {
        "reports": reports,
        "status_choices": Report.STATUS_CHOICES,
        "current_status": current_status,
    })


@login_required
def workspace_report_create(request):
    if request.method == "POST":
        template = get_object_or_404(ReportTemplate, pk=request.POST.get("template"))
        report = Report.objects.create(
            template=template,
            title=request.POST.get("title", "Без названия"),
            subtitle=request.POST.get("subtitle", ""),
            created_by=request.user,
        )
        # Set M2M
        corridor_ids = request.POST.getlist("corridors")
        country_ids = request.POST.getlist("countries")
        if corridor_ids:
            report.corridors.set(corridor_ids)
        if country_ids:
            report.countries.set(country_ids)

        # Create default sections from template config
        for i, sec_config in enumerate(template.sections_config or []):
            ReportSection.objects.create(
                report=report,
                order=i + 1,
                section_type=sec_config.get("type", "text"),
                title=sec_config.get("title", ""),
            )

        return redirect("workspace-report-edit", pk=report.pk)

    return render(request, "workspace/report_create.html", {
        "templates": ReportTemplate.objects.filter(is_active=True),
        "corridors": TradeCorridor.objects.filter(is_active=True),
        "countries": Country.objects.all(),
    })


@login_required
def workspace_report_edit(request, pk):
    report = get_object_or_404(
        Report.objects.prefetch_related("sections", "corridors", "countries"),
        pk=pk,
        created_by=request.user,
    )
    sections = report.sections.order_by("order")
    return render(request, "workspace/report_editor.html", {
        "report": report,
        "sections": sections,
        "section_types": ReportSection.SECTION_TYPES,
    })


# --- HTMX endpoints ---

@login_required
@require_POST
def save_report_meta(request, pk):
    report = get_object_or_404(Report, pk=pk, created_by=request.user)
    if "executive_summary" in request.POST:
        report.executive_summary = request.POST["executive_summary"]
        report.save(update_fields=["executive_summary", "updated_at"])
    return HttpResponse("OK")


@login_required
@require_POST
def save_section(request, pk):
    section = get_object_or_404(
        ReportSection, pk=pk, report__created_by=request.user
    )
    if "content" in request.POST:
        section.content = request.POST["content"]
    if "analyst_notes" in request.POST:
        section.analyst_notes = request.POST["analyst_notes"]
    section.save()
    return HttpResponse("OK")


@login_required
@require_POST
def add_section(request, report_pk):
    report = get_object_or_404(Report, pk=report_pk, created_by=request.user)
    section_type = request.POST.get("section_type", "text")
    order = int(request.POST.get("order", 1))
    section = ReportSection.objects.create(
        report=report,
        section_type=section_type,
        order=order,
    )
    return redirect("workspace-report-edit", pk=report.pk)


def htmx_corridor_scores(request):
    """HTMX partial: latest corridor scores"""
    corridor_ids = request.GET.get("corridor_id", "").split(",")
    scores = []
    corridors = TradeCorridor.objects.filter(is_active=True)
    if corridor_ids and corridor_ids[0]:
        corridors = corridors.filter(pk__in=[int(i) for i in corridor_ids if i.isdigit()])
    for corridor in corridors:
        score = RouteScore.objects.filter(corridor=corridor).order_by("-calculated_at").first()
        if score:
            scores.append(score)
    return render(request, "workspace/htmx/corridor_scores.html", {"scores": scores})


def htmx_risk_factors(request):
    """HTMX partial: risk factors table"""
    corridor_ids = request.GET.get("corridor_id", "").split(",")
    risk_factors = RiskFactor.objects.filter(is_active=True).order_by("-impact_score")[:15]
    if corridor_ids and corridor_ids[0]:
        risk_factors = risk_factors.filter(
            corridor_id__in=[int(i) for i in corridor_ids if i.isdigit()]
        )
    return render(request, "workspace/htmx/risk_factors.html", {"risk_factors": risk_factors})


def htmx_recent_alerts(request):
    """HTMX partial: recent high-impact risk factors"""
    alerts = RiskFactor.objects.filter(
        is_active=True, impact_score__gte=3
    ).order_by("-created_at")[:8]
    return render(request, "workspace/htmx/recent_alerts.html", {"alerts": alerts})


def htmx_recent_news(request):
    """HTMX partial: recent news items"""
    items = NewsItem.objects.order_by("-published_at")[:8]
    return render(request, "workspace/htmx/recent_news.html", {"items": items})


def htmx_sanction_check(request):
    """HTMX partial: sanction search results"""
    q = request.GET.get("q", "").strip()
    entries = []
    if len(q) >= 2:
        entries = SanctionEntry.objects.filter(
            Q(name_primary__icontains=q) | Q(name_aliases__icontains=q),
            is_active=True,
        ).select_related("source")[:30]
    return render(request, "workspace/htmx/sanction_results.html", {
        "entries": entries,
        "query": q,
    })


def htmx_scenarios(request):
    """HTMX partial: scenarios table"""
    corridor_ids = request.GET.get("corridor_id", "").split(",")
    scenarios = Scenario.objects.select_related("corridor").order_by("corridor", "plan_code")
    if corridor_ids and corridor_ids[0]:
        scenarios = scenarios.filter(
            corridor_id__in=[int(i) for i in corridor_ids if i.isdigit()]
        )
    return render(request, "workspace/htmx/scenarios.html", {"scenarios": scenarios})
