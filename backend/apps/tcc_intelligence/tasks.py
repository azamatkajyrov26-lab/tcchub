import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def recalculate_all_route_scores(self):
    """Пересчитывает RouteScore для всех активных коридоров"""
    from apps.tcc_core.models import TradeCorridor
    from apps.tcc_intelligence.scoring import calculate_corridor_risk

    corridors = TradeCorridor.objects.filter(is_active=True)
    results = []

    for corridor in corridors:
        try:
            score = calculate_corridor_risk(corridor.id)
            results.append(
                f"{corridor.code}: {score.score_total:.3f} ({score.risk_level})"
            )
            logger.info("Recalculated score for %s: %s", corridor.code, score.risk_level)
        except Exception as e:
            logger.error("Failed to calculate score for %s: %s", corridor.code, e)

    logger.info("Route scores recalculated: %s", ", ".join(results))
    return results
