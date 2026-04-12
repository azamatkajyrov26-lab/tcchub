from django.db import migrations


EXPERTS = [
    ("Рустем Бисалиев", "Основатель и CEO",
     "Эксперт в стратегическом управлении цепями поставок",
     "https://optim.tildacdn.pro/tild3035-6432-4333-b236-383634636339/-/resize/385x/-/format/webp/man.png.webp",
     ""),
    ("Айслу Тайсаринова", "Логистика и транспорт",
     "Эксперт по логистике и транспортному планированию. Опыт 23+ лет",
     "", "АТ"),
    ("Рустам Хуснутдинов", "Проектная логистика",
     "Эксперт по проектной логистике и снабжению. Опыт 25+ лет",
     "", "РХ"),
    ("Оксана Сорокина", "Международная логистика",
     "Эксперт в международной логистике и авиационных перевозках. Опыт 22+ лет",
     "", "ОС"),
]

SOLUTIONS = [
    ("Стратегические сессии для компаний",
     "Экспертное сопровождение, оценка цепей поставок, моделирование сценариев и разработка решений для повышения устойчивости.",
     ["Стратегические сессии и экспертное сопровождение",
      "Моделирование сценариев цепей поставок",
      "Решения для инфраструктурных и международных проектов"],
     "c1"),
    ("Анализ цепей поставок",
     "Комплексный аудит supply chain — от поставщиков до конечного потребителя. Узкие места, оптимизация, эффективность.",
     ["Аудит цепи и ключевых звеньев",
      "Оценка стоимости, сроков, надёжности",
      "Бенчмаркинг с лучшими практиками отрасли",
      "Рекомендации по снижению затрат"],
     "c2"),
    ("Логистические риски",
     "Карта рисков по каждому звену: санкции, геополитика, инфраструктура, зависимость от контрагентов.",
     ["Карта рисков по звеньям", "Санкционный скрининг", "Планы митигации"],
     "c3"),
    ("Альтернативные маршруты",
     "Средний коридор, Север-Юг, мультимодальные схемы — проектирование и оценка маршрутов.",
     ["Сравнение маршрутов", "Готовность инфраструктуры", "Сценарии перемаршрутизации"],
     "c4"),
    ("Выход на новые рынки",
     "Сопровождение при выходе на рынки ЦА, Каспия, Китая и Европы. От анализа до B2B-связей.",
     ["Анализ ёмкости и барьеров", "Регуляторика и таможня", "B2B-встречи, поиск партнёров"],
     "c5"),
]


def seed(apps, schema_editor):
    SiteItem = apps.get_model("landing", "SiteItem")

    for order, (name, role, desc, img, initials) in enumerate(EXPERTS, start=1):
        SiteItem.objects.update_or_create(
            category="expert", title=name,
            defaults={
                "subtitle": role, "description": desc,
                "image_url": img, "data": {"initials": initials},
                "order": order, "is_published": True,
            },
        )

    for order, (title, desc, bullets, cls) in enumerate(SOLUTIONS, start=1):
        SiteItem.objects.update_or_create(
            category="solution", title=title,
            defaults={
                "description": desc,
                "data": {"bullets": bullets, "css_class": cls},
                "order": order, "is_published": True,
            },
        )


def unseed(apps, schema_editor):
    SiteItem = apps.get_model("landing", "SiteItem")
    SiteItem.objects.filter(category__in=["expert", "solution"]).delete()


class Migration(migrations.Migration):
    dependencies = [("landing", "0008_alter_siteitem_category")]
    operations = [migrations.RunPython(seed, unseed)]
