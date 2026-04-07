"""
Load initial intelligence data: scenarios and risk factors.
"""

from datetime import date

from django.core.management.base import BaseCommand

from apps.tcc_core.models import Country, TradeCorridor
from apps.tcc_intelligence.models import RiskFactor, Scenario


SCENARIOS = [
    # TMTM
    {
        "corridor_code": "TMTM",
        "plan_code": "A",
        "label": "Основной — через Актау",
        "description": "Стандартный маршрут через Хоргос → Актау → Баку. Наиболее освоенный, регулярные паромные рейсы.",
        "cost_index": 1.0,
        "transit_days_min": 18,
        "transit_days_max": 25,
        "reliability_score": 0.75,
        "risk_score": 0.2,
        "is_recommended": True,
    },
    {
        "corridor_code": "TMTM",
        "plan_code": "B",
        "label": "Резервный — через Курык",
        "description": "Маршрут через новый порт Курык с Ro-Ro терминалом. Меньше загруженность, но ограниченная частота.",
        "cost_index": 1.1,
        "transit_days_min": 20,
        "transit_days_max": 28,
        "reliability_score": 0.65,
        "risk_score": 0.25,
        "is_recommended": False,
    },
    {
        "corridor_code": "TMTM",
        "plan_code": "C",
        "label": "Кризисный — через Туркменбаши",
        "description": "Транзит через Туркменистан при блокировке казахстанских портов. Сложная таможня.",
        "cost_index": 1.4,
        "transit_days_min": 25,
        "transit_days_max": 40,
        "reliability_score": 0.4,
        "risk_score": 0.6,
        "is_recommended": False,
    },
    # NORTHERN
    {
        "corridor_code": "NORTHERN",
        "plan_code": "A",
        "label": "Транссиб — стандартный",
        "description": "Классический маршрут через Транссибирскую магистраль. Быстрый но высокий санкционный риск.",
        "cost_index": 0.8,
        "transit_days_min": 14,
        "transit_days_max": 18,
        "reliability_score": 0.5,
        "risk_score": 0.8,
        "is_recommended": False,
    },
    {
        "corridor_code": "NORTHERN",
        "plan_code": "B",
        "label": "Обход через Казахстан",
        "description": "Обходной маршрут минуя российскую территорию через Казахстан → ТМТМ.",
        "cost_index": 1.3,
        "transit_days_min": 22,
        "transit_days_max": 30,
        "reliability_score": 0.7,
        "risk_score": 0.3,
        "is_recommended": True,
    },
    # INSTC
    {
        "corridor_code": "INSTC",
        "plan_code": "A",
        "label": "Западная ветка — через Азербайджан",
        "description": "Индия → Иран → Азербайджан → Россия. Наиболее развитый сегмент INSTC.",
        "cost_index": 1.0,
        "transit_days_min": 20,
        "transit_days_max": 30,
        "reliability_score": 0.55,
        "risk_score": 0.6,
        "is_recommended": False,
    },
    {
        "corridor_code": "INSTC",
        "plan_code": "B",
        "label": "Транскаспийская ветка",
        "description": "Индия → Иран → Каспий (паром) → Казахстан. Обход санкционных территорий.",
        "cost_index": 1.2,
        "transit_days_min": 25,
        "transit_days_max": 35,
        "reliability_score": 0.45,
        "risk_score": 0.45,
        "is_recommended": True,
    },
]

RISK_FACTORS = [
    # Sanctions risks
    {
        "corridor_code": "NORTHERN",
        "country_iso2": "RU",
        "risk_category": "sanctions",
        "severity": 9,
        "probability": 10,
        "title": "Всеобъемлющие санкции против России",
        "description": "ЕС, США, Великобритания ввели масштабные санкции против РФ, ограничивающие транзит и финансовые операции.",
        "evidence": "OFAC SDN List, EU Regulation 833/2014, UK sanctions regime",
        "mitigation": "Переход на Средний коридор (ТМТМ), использование альтернативных финансовых инструментов",
        "source_type": "auto_sanction",
    },
    {
        "corridor_code": "INSTC",
        "country_iso2": "IR",
        "risk_category": "sanctions",
        "severity": 8,
        "probability": 9,
        "title": "Санкции против Ирана",
        "description": "Вторичные санкции США против Ирана затрагивают транзитные операции через INSTC.",
        "evidence": "OFAC Iran sanctions program, Executive Order 13846",
        "mitigation": "Использование специальных торговых механизмов, партнёрство с индийскими операторами",
        "source_type": "auto_sanction",
    },
    # Geopolitical
    {
        "corridor_code": "TMTM",
        "risk_category": "geopolitical",
        "severity": 4,
        "probability": 3,
        "title": "Каспийский транзит — геополитическая неопределённость",
        "description": "Споры о правовом статусе Каспийского моря могут влиять на паромные маршруты.",
        "evidence": "Конвенция о правовом статусе Каспия 2018",
        "mitigation": "Диверсификация портов (Актау + Курык), страхование грузов",
        "source_type": "manual_analyst",
    },
    # Infrastructure
    {
        "corridor_code": "TMTM",
        "risk_category": "infrastructure",
        "severity": 6,
        "probability": 7,
        "title": "Ограниченная пропускная способность паромов на Каспии",
        "description": "Дефицит паромов и очереди в портах Актау/Курык. Средний простой 3-7 дней.",
        "evidence": "Данные Middle Corridor Alliance, отчёты KTZ Express 2024",
        "mitigation": "Предварительное бронирование слотов, использование контейнерных маршрутов",
        "source_type": "manual_analyst",
    },
    {
        "corridor_code": "TMTM",
        "risk_category": "infrastructure",
        "severity": 3,
        "probability": 4,
        "title": "Модернизация BTK ж/д (Баку-Тбилиси-Карс)",
        "description": "Расширение пропускной способности BTK с 1 до 5 млн тонн/год. Временные ограничения.",
        "evidence": "ADY Railways, Georgian Railway инвестиционные планы",
        "mitigation": "Планирование отправок с учётом графика работ",
        "source_type": "manual_analyst",
    },
    # Regulatory
    {
        "corridor_code": "TMTM",
        "country_iso2": "KZ",
        "risk_category": "regulatory",
        "severity": 3,
        "probability": 5,
        "title": "Таможенные процедуры Казахстана",
        "description": "Сложная таможенная документация, необходимость специальных разрешений для ряда товарных групп.",
        "evidence": "Таможенный кодекс ЕАЭС, НПА МФ РК",
        "mitigation": "Использование таможенных брокеров, предварительное декларирование",
        "source_type": "manual_analyst",
    },
    # Financial
    {
        "corridor_code": "TMTM",
        "risk_category": "financial",
        "severity": 5,
        "probability": 6,
        "title": "Волатильность тарифов на фрахт Каспия",
        "description": "Стоимость паромной переправы колеблется на 20-40% в зависимости от сезона и загрузки.",
        "evidence": "Мониторинг тарифов TransCaspian Cargo 2024",
        "mitigation": "Долгосрочные контракты с операторами, хеджирование валютных рисков",
        "source_type": "manual_analyst",
    },
]


class Command(BaseCommand):
    help = "Load initial TCC intelligence data: scenarios and risk factors"

    def handle(self, *args, **options):
        corridor_map = {c.code: c for c in TradeCorridor.objects.all()}
        country_map = {c.iso2: c for c in Country.objects.all()}

        # Scenarios
        sc_count = 0
        for s in SCENARIOS:
            corridor = corridor_map.get(s["corridor_code"])
            if not corridor:
                self.stderr.write(f"  Corridor {s['corridor_code']} not found")
                continue
            obj, created = Scenario.objects.update_or_create(
                corridor=corridor,
                plan_code=s["plan_code"],
                defaults={
                    "label": s["label"],
                    "description": s["description"],
                    "cost_index": s["cost_index"],
                    "transit_days_min": s["transit_days_min"],
                    "transit_days_max": s["transit_days_max"],
                    "reliability_score": s["reliability_score"],
                    "risk_score": s["risk_score"],
                    "is_recommended": s["is_recommended"],
                },
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  Scenario {s['corridor_code']} Plan {s['plan_code']} — {status}")
            sc_count += 1
        self.stdout.write(self.style.SUCCESS(f"Scenarios: {sc_count}"))

        # Risk Factors
        rf_count = 0
        for rf in RISK_FACTORS:
            corridor = corridor_map.get(rf.get("corridor_code"))
            country = country_map.get(rf.get("country_iso2"))

            obj, created = RiskFactor.objects.update_or_create(
                title=rf["title"],
                defaults={
                    "corridor": corridor,
                    "country": country,
                    "risk_category": rf["risk_category"],
                    "severity": rf["severity"],
                    "probability": rf["probability"],
                    "impact_score": rf["severity"] * rf["probability"] / 10.0,
                    "description": rf["description"],
                    "evidence": rf.get("evidence", ""),
                    "mitigation": rf.get("mitigation", ""),
                    "source_type": rf["source_type"],
                    "valid_from": date(2024, 1, 1),
                    "is_active": True,
                },
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  RiskFactor: {rf['title'][:50]} — {status}")
            rf_count += 1
        self.stdout.write(self.style.SUCCESS(f"Risk factors: {rf_count}"))

        self.stdout.write(self.style.SUCCESS("\nTCC Intelligence data loaded!"))
