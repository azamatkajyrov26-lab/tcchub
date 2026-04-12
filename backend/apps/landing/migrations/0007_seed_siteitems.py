from django.db import migrations


ARTICLES = [
    ("transkaspiyskiy-marshrut", "Транскаспийский маршрут: пятикратный рост за 7 лет",
     "Отраслевой обзор",
     "Транскаспийский международный транспортный маршрут (Средний коридор) достиг объёма 4.5 млн тонн грузоперевозок. Разрыв инвестиций в инфраструктуру оценивается в EUR 18.5 млрд.",
     "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1200&h=700&fit=crop",
     ["4.5 млн тонн", "EUR 18.5 млрд"], True),
    ("sanktsii-peremarshrutizatsiya", "Санкции и перемаршрутизация: новая карта Евразии",
     "Статья",
     "Трафик через Суэц сократился на 90%, ставки фрахта выросли на 80%. Как давление формирует новые торговые коридоры.",
     "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=400&fit=crop",
     ["Суэц −90%", "Фрахт +80%"], False),
    ("konteynernyy-rynok-evrazii", "Контейнерный рынок Евразии 2025–2026",
     "Исследование",
     "Направление Китай-Европа сократилось на 18%, Средний коридор вырос на 14%. Обзор ключевых контейнерных потоков.",
     "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600&h=400&fit=crop",
     ["Китай-Европа −18%", "СК +14%"], False),
    ("koridor-sever-yug", "Коридор Север-Юг: 26.9 млн тонн",
     "Отчёт",
     "INSTC показал рост на 19%. Пакистан присоединился, расширяя географию маршрута.",
     "https://images.unsplash.com/photo-1605732562742-3023a888e56e?w=600&h=400&fit=crop",
     ["INSTC +19%", "26.9 млн т"], False),
    ("tsifrovaya-transformatsiya", "Цифровая трансформация логистики Центральной Азии",
     "Статья",
     "Внедрение ASYCUDAWorld, рост e-commerce и цифровых платформ меняют логистическую инфраструктуру региона.",
     "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=400&fit=crop",
     ["ASYCUDAWorld", "E-commerce"], False),
    ("kazakhstan-tranzitnyy-hab", "Казахстан: 36.9 млн тонн транзита",
     "Исследование",
     "Хоргос обработал 372K TEU. Казахстан укрепляет позиции ключевого транзитного хаба Евразии.",
     "https://images.unsplash.com/photo-1545128485-c400e7702796?w=600&h=400&fit=crop",
     ["36.9 млн т", "372K TEU"], False),
    ("bri-2025", "BRI 2025: рекордные $128 млрд контрактов",
     "Обзор",
     "«Один пояс, один путь» показала рост на 81%. Анализ влияния на логистику Центральной Азии.",
     "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=600&h=400&fit=crop",
     ["$128 млрд", "+81%"], False),
    ("krasnoye-more-krizis", "Красное море: как кризис меняет глобальные маршруты",
     "Отчёт",
     "Трафик через Суэцкий канал упал на 90%. Перераспределение грузопотоков создаёт возможности для сухопутных коридоров.",
     "https://images.unsplash.com/photo-1524522173746-f628baad3644?w=600&h=400&fit=crop",
     ["Суэц −90%", "Альтернативы"], False),
]


PARTNERS_INTL = [
    ("New Silk Road Network", "Международная сеть развития Нового Шёлкового пути",
     "https://cdn.prod.website-files.com/63d8b07e8e897ea292020f31/63d8c1a749fdb30c3fac59ae_Frame%201.svg",
     "https://www.newsilkroadnetwork.com/"),
    ("PetroCouncil Kazakhstan", "Нефтегазовый Совет Казахстана",
     "https://petrocouncil.kz/storage/app/media/logo.png",
     "https://petrocouncil.kz/ru"),
    ("EUCA Alliance", "Объединение ведущих логистических компаний Евразии",
     "https://euca-alliance.com/wp-content/uploads/2023/08/Black-2.png",
     "https://euca-alliance.com/"),
]

PARTNERS_EDU = [
    ("Атырауский университет нефти и газа", "им. С. Утебаева",
     "https://aogu.edu.kz/local/templates/aogu_main/img/favicon.png",
     "https://aogu.edu.kz/"),
    ("Казахстанско-Немецкий Университет", "DKU · Алматы",
     "https://dku.kz/storage/app/media/logo.png",
     "https://dku.kz/ru"),
    ("МКТУ им. Ходжи Ахмеда Ясави", "Международный казахско-турецкий университет",
     "https://yu.edu.kz/wp-content/uploads/2023/08/blue_logo.png",
     "https://yu.edu.kz/"),
    ("Высший колледж APEC PetroTechnic", "Атырау",
     "https://apec.edu.kz/assets/main_logo.png",
     "https://apec.edu.kz/"),
    ("Satbayev University", "Казахский национальный исследовательский технический университет",
     "https://satbayev.university/files/img/university/logo-nav-blue.svg",
     "https://satbayev.university/en"),
]


PROJECTS_MC = [
    ("Развитие Транскаспийского маршрута (ТМТМ)",
     "Экспертная поддержка инфраструктуры Среднего коридора. Грузопоток вырос в 5 раз за 7 лет до 4.5 млн тонн. ЕС выделил €12 млрд на связность Центральной Азии.",
     "Активный"),
    ("Аналитика маршрутов Каспийского региона",
     "Мониторинг и анализ грузопотоков через порты Актау и Курык. Оценка пропускной способности и узких мест транскаспийского транзита.",
     "Активный"),
    ("Карта коридоров Центральной Азии",
     "Визуализация и аналитика основных транспортных маршрутов: железнодорожные, автомобильные, морские и мультимодальные коридоры региона.",
     "В разработке"),
]

PROJECTS_INTL = [
    ("Партнёрство с EUCA Alliance",
     "Сотрудничество с объединением ведущих логистических компаний Евразии для развития международных транспортных коридоров.",
     "Активный"),
    ("Интеграция логистических платформ Евразии",
     "Создание единой информационной среды для участников логистической цепи в Центральной Азии и на Кавказе.",
     "Активный"),
    ("Развитие мультимодальных перевозок",
     "Проектирование оптимальных мультимодальных маршрутов с учётом тарифов, сроков доставки и инфраструктурных ограничений региона.",
     "В разработке"),
]

PROJECTS_RESEARCH = [
    ("Исследование логистики Евразии",
     "Комплексная аналитическая программа: торговые коридоры, инфраструктурные проекты, логистические тренды. Регулярные отчёты и экспертные обзоры.",
     "Активный"),
    ("BRI Logistics Research",
     "Исследование влияния инициативы «Пояс и путь» на логистическую инфраструктуру Центральной Азии. Сценарии развития до 2035 года.",
     "Активный"),
    ("Санкционная аналитика и адаптация маршрутов",
     "Мониторинг санкционных режимов и их влияния на логистические цепочки. Разработка альтернативных маршрутов и стратегий адаптации.",
     "Активный"),
]


PROGRAMS = [
    ("Курсы", "Онлайн-программы",
     "Базовые и продвинутые курсы по логистике, SCM, таможенному оформлению и транспортному праву. Сертификация по завершении."),
    ("Практикумы", "Интенсивы",
     "Практические воркшопы с разбором реальных кейсов. Работа с документами, расчёт тарифов, проектирование маршрутов."),
    ("Корпоративные программы", "Для компаний",
     "Индивидуальные программы обучения сотрудников логистических, ВЭД и закупочных подразделений. Аудит компетенций."),
]


def seed(apps, schema_editor):
    SiteItem = apps.get_model("landing", "SiteItem")

    # Articles
    for order, (slug, title, tag, desc, img, metrics, featured) in enumerate(ARTICLES, start=1):
        SiteItem.objects.update_or_create(
            category="article", slug=slug,
            defaults={
                "title": title, "tag": tag, "description": desc,
                "image_url": img, "link_url": f"/analytics/{slug}/",
                "data": {"metrics": metrics, "featured": featured},
                "order": order, "is_published": True,
            },
        )

    # Partners — international
    for order, (name, desc, logo, url) in enumerate(PARTNERS_INTL, start=1):
        SiteItem.objects.update_or_create(
            category="partner", subcategory="international", title=name,
            defaults={"description": desc, "image_url": logo, "link_url": url,
                      "order": order, "is_published": True},
        )

    # Partners — education
    for order, (name, desc, logo, url) in enumerate(PARTNERS_EDU, start=1):
        SiteItem.objects.update_or_create(
            category="partner", subcategory="education", title=name,
            defaults={"description": desc, "image_url": logo, "link_url": url,
                      "order": order, "is_published": True},
        )

    # Projects — middle corridor
    for order, (title, desc, status) in enumerate(PROJECTS_MC, start=1):
        SiteItem.objects.update_or_create(
            category="project", subcategory="middle_corridor", title=title,
            defaults={"description": desc, "status": status,
                      "order": order, "is_published": True},
        )

    # Projects — international
    for order, (title, desc, status) in enumerate(PROJECTS_INTL, start=1):
        SiteItem.objects.update_or_create(
            category="project", subcategory="international", title=title,
            defaults={"description": desc, "status": status,
                      "order": order + 3, "is_published": True},
        )

    # Projects — research
    for order, (title, desc, status) in enumerate(PROJECTS_RESEARCH, start=1):
        SiteItem.objects.update_or_create(
            category="project", subcategory="research", title=title,
            defaults={"description": desc, "status": status,
                      "order": order + 6, "is_published": True},
        )

    # Programs
    for order, (title, subtitle, desc) in enumerate(PROGRAMS, start=1):
        SiteItem.objects.update_or_create(
            category="program", title=title,
            defaults={"subtitle": subtitle, "description": desc,
                      "order": order, "is_published": True},
        )


def unseed(apps, schema_editor):
    SiteItem = apps.get_model("landing", "SiteItem")
    SiteItem.objects.filter(category__in=["article", "partner", "project", "program"]).delete()


class Migration(migrations.Migration):
    dependencies = [("landing", "0006_siteitem")]
    operations = [migrations.RunPython(seed, unseed)]
