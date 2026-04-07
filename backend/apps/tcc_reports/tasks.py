import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_report_pdf_task(report_id: int):
    """Celery task: генерация PDF отчёта"""
    from apps.tcc_reports.pdf_generator import generate_report_pdf

    try:
        url = generate_report_pdf(report_id)
        logger.info("PDF generated for report #%d: %s", report_id, url)
        return url
    except Exception as e:
        logger.error("PDF generation failed for report #%d: %s", report_id, e)
        raise
