import csv
from datetime import date

from django.http import HttpResponse


def _csv_response(filename: str) -> HttpResponse:
    """Create an HttpResponse configured for CSV download with UTF-8 BOM."""
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    return response


def export_route_scores_csv(request):
    from apps.tcc_intelligence.models import RouteScore

    today = date.today().isoformat()
    filename = f"tcc_route_scores_{today}.csv"
    response = _csv_response(filename)
    writer = csv.writer(response)

    writer.writerow([
        "Corridor", "Code", "Total Score", "Sanctions", "Geopolitical",
        "Infrastructure", "Regulatory", "Financial", "Risk Level",
        "Calculated At",
    ])

    qs = RouteScore.objects.select_related("corridor")

    corridor_id = request.GET.get("corridor_id")
    if corridor_id:
        qs = qs.filter(corridor_id=corridor_id)

    for obj in qs.iterator():
        writer.writerow([
            obj.corridor.name,
            obj.corridor.code,
            obj.score_total,
            obj.score_sanctions,
            obj.score_geopolitical,
            obj.score_infrastructure,
            obj.score_regulatory,
            obj.score_financial,
            obj.get_risk_level_display(),
            obj.calculated_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


def export_risk_factors_csv(request):
    from apps.tcc_intelligence.models import RiskFactor

    today = date.today().isoformat()
    filename = f"tcc_risk_factors_{today}.csv"
    response = _csv_response(filename)
    writer = csv.writer(response)

    writer.writerow([
        "Title", "Category", "Severity", "Probability", "Impact Score",
        "Corridor", "Country", "Node", "Source", "Valid From", "Valid Until",
        "Active",
    ])

    qs = RiskFactor.objects.select_related("corridor", "country", "node")

    risk_category = request.GET.get("risk_category")
    if risk_category:
        qs = qs.filter(risk_category=risk_category)

    is_active = request.GET.get("is_active", "true")
    if is_active.lower() in ("true", "1"):
        qs = qs.filter(is_active=True)
    elif is_active.lower() in ("false", "0"):
        qs = qs.filter(is_active=False)

    for obj in qs.iterator():
        writer.writerow([
            obj.title,
            obj.get_risk_category_display(),
            obj.severity,
            obj.probability,
            obj.impact_score,
            obj.corridor.name if obj.corridor else "",
            obj.country.name_en if obj.country else "",
            obj.node.name if obj.node else "",
            obj.get_source_type_display(),
            obj.valid_from.isoformat() if obj.valid_from else "",
            obj.valid_until.isoformat() if obj.valid_until else "",
            "Yes" if obj.is_active else "No",
        ])

    return response


def export_trade_flows_csv(request):
    from apps.tcc_data.models import TradeFlow

    today = date.today().isoformat()
    filename = f"tcc_trade_flows_{today}.csv"
    response = _csv_response(filename)
    writer = csv.writer(response)

    writer.writerow([
        "Reporter", "Partner", "Year", "HS Code", "Flow Type",
        "Value USD", "Weight KG",
    ])

    qs = TradeFlow.objects.select_related("reporter_country", "partner_country")

    year = request.GET.get("year")
    if year:
        qs = qs.filter(year=year)

    reporter = request.GET.get("reporter")
    if reporter:
        qs = qs.filter(reporter_country__iso2=reporter.upper())

    for obj in qs.iterator():
        writer.writerow([
            obj.reporter_country.name_en,
            obj.partner_country.name_en,
            obj.year,
            obj.hs_code,
            obj.get_flow_type_display(),
            obj.value_usd,
            obj.weight_kg or "",
        ])

    return response


def export_sanctions_csv(request):
    from apps.tcc_data.models import SanctionEntry

    today = date.today().isoformat()
    filename = f"tcc_sanctions_{today}.csv"
    response = _csv_response(filename)
    writer = csv.writer(response)

    writer.writerow([
        "Name", "Entity Type", "Source", "Country", "Program", "Added Date",
    ])

    qs = SanctionEntry.objects.select_related("source")

    for obj in qs.iterator():
        writer.writerow([
            obj.name_primary,
            obj.get_entity_type_display(),
            obj.source.name,
            ", ".join(obj.countries) if obj.countries else "",
            obj.program,
            obj.listing_date.isoformat() if obj.listing_date else "",
        ])

    return response
