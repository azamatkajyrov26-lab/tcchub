"""
Scoring engine — рассчитывает риск-скор для торговых коридоров.

Веса:
  sanctions:      30%
  geopolitical:   20%
  infrastructure: 25%
  regulatory:     15%
  financial:      10%

Все компоненты нормализованы 0.0–1.0 (1.0 = максимальный риск).
"""

from apps.tcc_intelligence.models import RiskFactor, RouteScore

SCORE_WEIGHTS = {
    "sanctions": 0.30,
    "geopolitical": 0.20,
    "infrastructure": 0.25,
    "regulatory": 0.15,
    "financial": 0.10,
}

SANCTION_LEVEL_MAP = {
    "none": 0.0,
    "low": 0.2,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}


def _calc_sanction_score(countries):
    """Среднее санкционного уровня стран коридора"""
    if not countries:
        return 0.0
    levels = [SANCTION_LEVEL_MAP.get(c.sanction_risk_level, 0) for c in countries]
    return sum(levels) / len(levels)


def _calc_geopolitical_score(countries, corridor):
    """
    Комбинация World Bank stability (если есть) и активных геополитических рисков.
    """
    # World Bank stability — инвертируем (низкий индекс = высокий риск)
    wb_scores = [c.wb_stability_index for c in countries if c.wb_stability_index is not None]
    wb_component = 0.5  # default if no data
    if wb_scores:
        avg_wb = sum(wb_scores) / len(wb_scores)
        # WB index usually -2.5 to 2.5, normalize to 0-1 risk
        wb_component = max(0, min(1, (2.5 - avg_wb) / 5.0))

    # Active geopolitical risk factors
    geo_factors = RiskFactor.objects.filter(
        corridor=corridor,
        risk_category="geopolitical",
        is_active=True,
    )
    factor_component = 0.0
    if geo_factors.exists():
        avg_impact = sum(f.impact_score for f in geo_factors) / geo_factors.count()
        factor_component = min(1.0, avg_impact / 10.0)

    return 0.5 * wb_component + 0.5 * factor_component


def _calc_infrastructure_score(corridor):
    """
    Оценка по статусам узлов коридора.
    operational=0, limited=0.3, suspended=0.7, closed=1.0
    """
    status_map = {
        "operational": 0.0,
        "limited": 0.3,
        "suspended": 0.7,
        "closed": 1.0,
    }
    nodes = corridor.nodes.all()
    if not nodes:
        return 0.0
    scores = [status_map.get(n.status, 0) for n in nodes]

    # Also consider emulated statuses
    from apps.tcc_emulator.models import EmulatedNodeStatus

    for node in nodes:
        latest = (
            EmulatedNodeStatus.objects.filter(node=node)
            .order_by("-date")
            .first()
        )
        if latest:
            # High utilization (>90%) = higher risk
            if latest.throughput_percent > 90:
                scores.append(0.6)
            elif latest.throughput_percent > 75:
                scores.append(0.3)

    return sum(scores) / len(scores) if scores else 0.0


def _calc_regulatory_score(countries, corridor):
    """Активные регуляторные риск-факторы"""
    reg_factors = RiskFactor.objects.filter(
        risk_category="regulatory",
        is_active=True,
    ).filter(
        models_Q_corridor_or_country(corridor, countries)
    )
    if not reg_factors.exists():
        return 0.1  # baseline
    avg_impact = sum(f.impact_score for f in reg_factors) / reg_factors.count()
    return min(1.0, avg_impact / 10.0)


def _calc_financial_score(countries):
    """IMF GDP growth и CPI — низкий рост / высокая коррупция = риск"""
    scores = []
    for c in countries:
        country_score = 0.3  # baseline
        if c.imf_gdp_growth is not None:
            # Negative growth = high risk
            if c.imf_gdp_growth < 0:
                country_score += 0.4
            elif c.imf_gdp_growth < 2:
                country_score += 0.2
        if c.ti_cpi_score is not None:
            # CPI 0-100, lower = more corrupt = higher risk
            country_score += max(0, (50 - c.ti_cpi_score) / 100.0)
        scores.append(min(1.0, country_score))
    return sum(scores) / len(scores) if scores else 0.3


def models_Q_corridor_or_country(corridor, countries):
    """Build Q filter for corridor or any of its countries"""
    from django.db.models import Q

    q = Q(corridor=corridor)
    for c in countries:
        q |= Q(country=c)
    return q


def calculate_corridor_risk(corridor_id: int) -> RouteScore:
    """Рассчитывает и сохраняет RouteScore для коридора"""
    from apps.tcc_core.models import TradeCorridor

    corridor = TradeCorridor.objects.prefetch_related("nodes__country").get(
        id=corridor_id
    )
    countries = list({n.country for n in corridor.nodes.all()})

    scores = {
        "sanctions": _calc_sanction_score(countries),
        "geopolitical": _calc_geopolitical_score(countries, corridor),
        "infrastructure": _calc_infrastructure_score(corridor),
        "regulatory": _calc_regulatory_score(countries, corridor),
        "financial": _calc_financial_score(countries),
    }

    total = sum(SCORE_WEIGHTS[k] * scores[k] for k in SCORE_WEIGHTS)
    risk_level = (
        "low" if total < 0.3
        else "medium" if total < 0.55
        else "high" if total < 0.75
        else "critical"
    )

    # Snapshot active factors
    factors = RiskFactor.objects.filter(
        is_active=True,
    ).filter(
        models_Q_corridor_or_country(corridor, countries)
    )
    factors_snapshot = [
        {
            "id": f.id,
            "title": f.title,
            "category": f.risk_category,
            "severity": f.severity,
            "probability": f.probability,
            "impact_score": f.impact_score,
        }
        for f in factors
    ]

    return RouteScore.objects.create(
        corridor=corridor,
        score_sanctions=scores["sanctions"],
        score_geopolitical=scores["geopolitical"],
        score_infrastructure=scores["infrastructure"],
        score_regulatory=scores["regulatory"],
        score_financial=scores["financial"],
        score_total=round(total, 4),
        risk_level=risk_level,
        weights=SCORE_WEIGHTS,
        factors_snapshot=factors_snapshot,
    )
