from celery import shared_task


@shared_task
def check_and_generate_alerts():
    from apps.tcc_core.models import RouteNode, TradeCorridor
    from apps.tcc_intelligence.models import RouteScore

    from .models import Alert

    new_alerts = 0

    # --- Score threshold alerts ---
    corridors = TradeCorridor.objects.all()
    for corridor in corridors:
        latest_score = (
            RouteScore.objects.filter(corridor=corridor)
            .order_by("-calculated_at")
            .first()
        )
        if latest_score is None:
            continue
        if latest_score.score_total <= 0.7:
            continue

        already_exists = Alert.objects.filter(
            alert_type="score_threshold",
            corridor=corridor,
            is_resolved=False,
        ).exists()
        if already_exists:
            continue

        severity = "critical" if latest_score.score_total > 0.85 else "warning"
        Alert.objects.create(
            alert_type="score_threshold",
            severity=severity,
            title=f"Порог оценки риска превышен для коридора «{corridor.name}»",
            description=(
                f"Общая оценка риска составляет {latest_score.score_total:.2f} "
                f"для коридора «{corridor.name}»."
            ),
            corridor=corridor,
            related_score=latest_score,
            data={"score_total": float(latest_score.score_total)},
        )
        new_alerts += 1

    # --- Node status alerts ---
    problem_nodes = RouteNode.objects.exclude(status="operational")
    for node in problem_nodes:
        already_exists = Alert.objects.filter(
            alert_type="node_status",
            node=node,
            is_resolved=False,
        ).exists()
        if already_exists:
            continue

        Alert.objects.create(
            alert_type="node_status",
            severity="warning",
            title=f"Узел «{node.name}» не в рабочем состоянии",
            description=(
                f"Узел маршрута «{node.name}» имеет статус «{node.status}»."
            ),
            node=node,
            data={"node_status": node.status},
        )
        new_alerts += 1

    return new_alerts
