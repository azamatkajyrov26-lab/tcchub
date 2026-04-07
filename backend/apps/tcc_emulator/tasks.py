import logging
import random
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def update_emulated_data():
    """Обновляет эмулированные данные для узлов без реального API"""
    from apps.tcc_emulator.models import EmulatedDataSource, EmulatedNodeStatus
    from apps.tcc_core.models import RouteNode

    today = date.today()
    count = 0

    for emu_source in EmulatedDataSource.objects.filter(
        data_source__is_active=True
    ).select_related("data_source"):
        # Get nodes marked as emulated
        nodes = RouteNode.objects.filter(is_emulated=True)

        for node in nodes:
            params = emu_source.base_parameters or {}
            base_throughput = params.get("base_throughput", 65)
            variance = params.get("variance", 15)

            throughput = max(0, min(100, base_throughput + random.randint(-variance, variance)))
            wait_hours = round(max(0.5, random.gauss(params.get("avg_wait", 4), 1.5)), 1)
            incidents = random.choices([0, 0, 0, 0, 1, 1, 2], k=1)[0]

            EmulatedNodeStatus.objects.update_or_create(
                node=node,
                date=today,
                defaults={
                    "emulation_source": emu_source,
                    "throughput_percent": throughput,
                    "avg_wait_hours": wait_hours,
                    "incidents_count": incidents,
                    "is_emulated": True,
                },
            )
            count += 1

    logger.info("Updated %d emulated node statuses", count)
    return count
