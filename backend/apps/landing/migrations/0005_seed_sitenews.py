from django.db import migrations
from datetime import date


SEED = [
    {
        "title": "New Vision Forum — ключевая площадка Центральной Азии",
        "kind": "мероприятие",
        "excerpt": "Лидеры отраслей, инвесторы и эксперты формируют контуры будущей экономики. TCC представила видение развития логистики региона.",
        "cover_url": "",
        "published_at": date(2025, 10, 1),
        "order": 1,
    },
    {
        "title": "Baku Energy Week / Translogistica Caspian",
        "kind": "мероприятие",
        "excerpt": "Баку — эпицентр энергетики и логистики. TCC выступила проводником между бизнесом, маршрутами Среднего коридора и развитием человеческого капитала.",
        "cover_url": "",
        "published_at": date(2025, 6, 1),
        "order": 2,
    },
    {
        "title": "Геоэкономика торговых маршрутов: взгляд из Центральной Азии",
        "kind": "статья",
        "excerpt": "Кризис в Красном море, санкционное давление и рост Среднего коридора создали уникальное окно возможностей для региона как транзитного хаба.",
        "cover_url": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600&h=400&fit=crop",
        "published_at": date(2025, 3, 15),
        "order": 3,
    },
    {
        "title": "Рустем Бисалиев: «Логистика Евразии — это экосистема знаний»",
        "kind": "интервью",
        "excerpt": "Основатель TCC о стратегии платформы, роли образования и почему будущее логистики Центральной Азии зависит от компетенций специалистов.",
        "cover_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600&h=400&fit=crop",
        "published_at": date(2025, 2, 10),
        "order": 4,
    },
    {
        "title": "BRI 2025: $128 млрд контрактов и сдвиг к зелёным технологиям",
        "kind": "исследование",
        "excerpt": "Китайские BRI-контракты выросли на 81% в 2024 году. Анализ влияния на логистические цепочки Евразии и новые инвестиционные приоритеты.",
        "cover_url": "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=600&h=400&fit=crop",
        "published_at": date(2025, 1, 20),
        "order": 5,
    },
    {
        "title": "Средний коридор: от пилотных проектов к стабильным грузопотокам",
        "kind": "статья",
        "excerpt": "Транскаспийский маршрут вышел на 4.5 млн тонн — пятикратный рост за 7 лет. Инвестиции в $3 млрд в казахстанский участок ТМТМ.",
        "cover_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=400&fit=crop",
        "published_at": date(2024, 12, 10),
        "order": 6,
    },
    {
        "title": "TCC HUB: обзор образовательной платформы",
        "kind": "видео",
        "excerpt": "Структура курсов, формат видеолекций, система сертификации и инструменты для развития компетенций в логистике и SCM.",
        "cover_url": "",
        "published_at": date(2025, 5, 1),
        "order": 7,
    },
    {
        "title": "Цифровизация таможни: опыт Казахстана и Узбекистана",
        "kind": "исследование",
        "excerpt": "Казахстан сократил время оформления на 40%, Узбекистан запустил единое окно. Какие уроки извлечь для всего региона.",
        "cover_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&h=400&fit=crop",
        "published_at": date(2024, 11, 15),
        "order": 8,
    },
]


def seed_news(apps, schema_editor):
    SiteNews = apps.get_model("landing", "SiteNews")
    for row in SEED:
        SiteNews.objects.update_or_create(
            title=row["title"],
            defaults={
                "kind": row["kind"],
                "excerpt": row["excerpt"],
                "body": "",
                "cover_url": row["cover_url"],
                "external_url": "",
                "published_at": row["published_at"],
                "is_published": True,
                "show_on_landing": False,
                "order": row["order"],
            },
        )


def unseed_news(apps, schema_editor):
    SiteNews = apps.get_model("landing", "SiteNews")
    SiteNews.objects.filter(title__in=[r["title"] for r in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("landing", "0004_sitenews")]
    operations = [migrations.RunPython(seed_news, unseed_news)]
