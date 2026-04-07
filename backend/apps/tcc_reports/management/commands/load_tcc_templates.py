"""
Load initial report templates.
"""

from django.core.management.base import BaseCommand

from apps.tcc_reports.models import ReportTemplate


TEMPLATES = [
    {
        "code": "ROUTE_ANALYSIS",
        "name": "Анализ маршрута",
        "description": "Полный анализ торгового коридора: риск-скор, сценарии, рекомендации.",
        "html_template": "reports/pdf/route_analysis.html",
        "sections_config": [
            {"type": "text", "title": "Введение"},
            {"type": "route_score", "title": "Риск-скор коридора"},
            {"type": "risk_table", "title": "Таблица рисков"},
            {"type": "scenario_comparison", "title": "Сравнение сценариев"},
            {"type": "map", "title": "Карта маршрута"},
            {"type": "text", "title": "Выводы и рекомендации"},
        ],
    },
    {
        "code": "COUNTRY_RISK",
        "name": "Страновой риск-профиль",
        "description": "Анализ рисков конкретной страны: санкции, стабильность, регулирование.",
        "html_template": "reports/pdf/country_risk.html",
        "sections_config": [
            {"type": "text", "title": "Обзор страны"},
            {"type": "country_profile", "title": "Экономический профиль"},
            {"type": "sanction_check", "title": "Санкционный скрининг"},
            {"type": "risk_table", "title": "Риск-факторы"},
            {"type": "text", "title": "Регуляторная среда"},
            {"type": "text", "title": "Рекомендации"},
        ],
    },
    {
        "code": "CORRIDOR_BRIEF",
        "name": "Коридорный брифинг",
        "description": "Краткий обзор состояния коридора для оперативного использования.",
        "html_template": "reports/pdf/corridor_brief.html",
        "sections_config": [
            {"type": "route_score", "title": "Текущий статус"},
            {"type": "risk_table", "title": "Ключевые риски"},
            {"type": "text", "title": "Оперативные заметки"},
        ],
    },
    {
        "code": "SANCTION_SCREENING",
        "name": "Санкционный скрининг",
        "description": "Проверка контрагентов по санкционным спискам OFAC, EU, UN.",
        "html_template": "reports/pdf/base_report.html",
        "sections_config": [
            {"type": "text", "title": "Объект проверки"},
            {"type": "sanction_check", "title": "Результаты скрининга"},
            {"type": "text", "title": "Заключение"},
        ],
    },
    {
        "code": "MARKET_OVERVIEW",
        "name": "Обзор рынка",
        "description": "Анализ торговых потоков, тарифов и тенденций на маршруте.",
        "html_template": "reports/pdf/base_report.html",
        "sections_config": [
            {"type": "text", "title": "Обзор рынка"},
            {"type": "trade_flow_chart", "title": "Торговые потоки"},
            {"type": "text", "title": "Тарифы и стоимость"},
            {"type": "scenario_comparison", "title": "Прогноз"},
            {"type": "text", "title": "Рекомендации"},
        ],
    },
]


class Command(BaseCommand):
    help = "Load initial report templates"

    def handle(self, *args, **options):
        for t in TEMPLATES:
            obj, created = ReportTemplate.objects.update_or_create(
                code=t["code"],
                defaults={
                    "name": t["name"],
                    "description": t["description"],
                    "html_template": t["html_template"],
                    "sections_config": t["sections_config"],
                },
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  Template {t['code']} — {status}")

        self.stdout.write(self.style.SUCCESS(f"Report templates: {len(TEMPLATES)}"))
