# -*- coding: utf-8 -*-
"""
Populate KZ/EN translations for DB-driven SiteItem content.

Translations are stored in SiteItem.data['i18n'] = {'kz': {...}, 'en': {...}}
and rendered as data-i18n-kz / data-i18n-en attributes via the `i18n_attr`
template tag (apps/landing/templatetags/cms.py). The Russian value rendered
server-side remains the source of truth; i18n.js swaps these in on language
change and falls back to RU when a value is missing.

Idempotent — merges into existing data['i18n'] without dropping other keys.

Run:  docker compose exec -T backend python manage.py shell < scripts/translate_siteitems.py

For experts the KZ name equals the RU name, so `title` is intentionally
omitted from the kz block (JS keeps the rendered Russian).
"""

TRANSLATIONS = {
    # ── EXPERTS (about + education) ──
    29: {  # Рустем Бисалиев
        "en": {"title": "Rustem Bisaliyev", "subtitle": "Founder & CEO",
               "description": "Expert in strategic supply chain management"},
        "kz": {"subtitle": "Құрылтайшы және CEO",
               "description": "Жеткізу тізбегін стратегиялық басқару жөніндегі сарапшы"},
    },
    30: {  # Айслу Тайсаринова
        "en": {"title": "Aislu Taisarinova", "subtitle": "Logistics and transport",
               "description": "Expert in logistics and transport planning. 23+ years of experience"},
        "kz": {"subtitle": "Логистика және көлік",
               "description": "Логистика және көлік жоспарлау жөніндегі сарапшы. 23+ жыл тәжірибе"},
    },
    31: {  # Рустам Хуснутдинов
        "en": {"title": "Rustam Khusnutdinov", "subtitle": "Project logistics",
               "description": "Expert in project logistics and supply. 25+ years of experience"},
        "kz": {"subtitle": "Жобалық логистика",
               "description": "Жобалық логистика және жабдықтау жөніндегі сарапшы. 25+ жыл тәжірибе"},
    },
    32: {  # Оксана Сорокина
        "en": {"title": "Oksana Sorokina", "subtitle": "International logistics",
               "description": "Expert in international logistics and air freight. 22+ years of experience"},
        "kz": {"subtitle": "Халықаралық логистика",
               "description": "Халықаралық логистика және авиатасымал жөніндегі сарапшы. 22+ жыл тәжірибе"},
    },
    56: {  # Наргиза Турарбек
        "en": {"title": "Nargiza Turarbek", "subtitle": "Recruitment and HR in logistics",
               "description": "Expert in recruitment and HR. Over 7 years of experience"},
        "kz": {"subtitle": "Логистикадағы рекрутинг және HR",
               "description": "Рекрутинг және HR саласындағы сарапшы. 7 жылдан астам тәжірибе"},
    },
    57: {  # Артем Чертищев
        "en": {"title": "Artem Chertishchev", "subtitle": "Dangerous goods",
               "description": "Expert in dangerous goods transport. Over 15 years of experience"},
        "kz": {"subtitle": "Қауіпті жүктер",
               "description": "Қауіпті жүктерді тасымалдау жөніндегі сарапшы. 15 жылдан астам жұмыс тәжірибесі"},
    },
    58: {  # Анастасия Подовинникова
        "en": {"title": "Anastasia Podovinnikova", "subtitle": "Supply Chain",
               "description": "Supply Chain and Procurement expert with 20 years of experience in international FMCG and pharmaceutical companies"},
        "kz": {"subtitle": "Supply Chain",
               "description": "Халықаралық FMCG және фармацевтика компанияларында 20 жылдық тәжірибесі бар Supply Chain және Procurement саласындағы сарапшы"},
    },
    59: {  # Элвис Робертс
        "en": {"title": "Elvis Roberts", "subtitle": "Oversized cargo",
               "description": "Expert in oversized cargo transport. Over 25 years of experience"},
        "kz": {"subtitle": "Габаритсіз жүктер",
               "description": "Габаритсіз жүктерді тасымалдау саласындағы сарапшы. 25 жылдан астам жұмыс тәжірибесі"},
    },
    60: {  # Акмарал Сатбергенова
        "en": {"title": "Akmaral Satbergenova", "subtitle": "Project logistics",
               "description": "Expert in project logistics. Over 20 years of experience"},
        "kz": {"subtitle": "Жобалық логистика",
               "description": "Жобалық логистика жөніндегі сарапшы. 20 жылдан астам жұмыс тәжірибесі"},
    },
    61: {  # Оксана Крисанова
        "en": {"title": "Oksana Krisanova", "subtitle": "Customs regulation",
               "description": "Expert in customs regulation and customs clearance, over 20 years of experience"},
        "kz": {"subtitle": "Кедендік реттеу",
               "description": "Кедендік реттеу және кедендік ресімдеу мәселелері жөніндегі сарапшы, 20 жылдан астам жұмыс тәжірибесі"},
    },

    # ── PARTNERS (description only; brand titles unchanged) ──
    9:  {"en": {"description": "International development network of the New Silk Road"},
         "kz": {"description": "Жаңа Жібек жолын дамытудың халықаралық желісі"}},
    12: {"en": {"description": "named after S. Utebayev"},
         "kz": {"description": "С. Өтебаев атындағы"}},
    49: {"en": {"description": "International logistics company"},
         "kz": {"description": "Халықаралық логистикалық компания"}},
    10: {"en": {"description": "Oil and Gas Council of Kazakhstan"},
         "kz": {"description": "Қазақстан мұнай-газ кеңесі"}},
    13: {"en": {"description": "DKU · Almaty"},
         "kz": {"description": "DKU · Алматы"}},
    50: {"en": {"description": "Transport and logistics company"},
         "kz": {"description": "Көлік-логистикалық компания"}},
    11: {"en": {"description": "Alliance of leading logistics companies in Eurasia"},
         "kz": {"description": "Еуразияның жетекші логистикалық компанияларының бірлестігі"}},
    15: {"en": {"description": "Atyrau"},
         "kz": {"description": "Атырау"}},
    38: {"en": {"description": "International consulting in aviation logistics and transport solutions"},
         "kz": {"description": "Авиациялық логистика және көлік шешімдері саласындағы халықаралық консалтинг"}},
    16: {"en": {"description": "Kazakh National Research Technical University"},
         "kz": {"description": "Қазақ ұлттық техникалық зерттеу университеті"}},
    39: {"en": {"description": "International logistics company specialising in integrated supply chains"},
         "kz": {"description": "Интеграцияланған жеткізу тізбектеріне маманданған халықаралық логистикалық компания"}},
    40: {"en": {"description": "Global alliance for project logistics and heavy-lift transport"},
         "kz": {"description": "Жобалық логистика және ауыр салмақты тасымалдың жаһандық альянсы"}},
    48: {"en": {"description": "Kazakhstan's leading business university in management, economics and entrepreneurship"},
         "kz": {"description": "Менеджмент, экономика және кәсіпкерлік саласындағы Қазақстанның жетекші бизнес-университеті"}},
    41: {"en": {"description": "Professional customs support and brokerage services"},
         "kz": {"description": "Кәсіби кедендік сүйемелдеу және брокерлік қызметтер"}},
    55: {"en": {"description": "Sh. Yessenov Caspian University of Technology and Engineering"},
         "kz": {"description": "Ш. Есенов атындағы Каспий технологиялар және инжиниринг университеті"}},
    42: {"en": {"description": "Digital solutions platform for logistics and supply chain management"},
         "kz": {"description": "Логистика және жеткізу тізбегін басқаруға арналған цифрлық шешімдер платформасы"}},
    43: {"en": {"description": "Expertise in dangerous goods transport and regulatory compliance"},
         "kz": {"description": "Қауіпті жүктерді тасымалдау және нормативтік талаптарды сақтау саласындағы сараптама"}},
    44: {"en": {"description": "Industrial park and logistics hub in Western Kazakhstan"},
         "kz": {"description": "Батыс Қазақстандағы индустриялық саябақ және логистикалық хаб"}},
    45: {"en": {"description": "International supply chain operator"},
         "kz": {"description": "Халықаралық жеткізу тізбегі операторы"}},
    46: {"en": {"description": "Reliability assurance for main pipelines and infrastructure facilities"},
         "kz": {"description": "Магистральдық құбырлар мен инфрақұрылым нысандарының сенімділігін қамтамасыз ету"}},
    51: {"en": {"description": "National airline of Kazakhstan"},
         "kz": {"description": "Қазақстанның ұлттық әуежолы"}},
    52: {"en": {"description": "International retail brand"},
         "kz": {"description": "Халықаралық ритейл-бренд"}},
    53: {"en": {"description": "Industrial holding"},
         "kz": {"description": "Өнеркәсіптік холдинг"}},
    54: {"en": {"description": "Rental and sale of special equipment in Kazakhstan"},
         "kz": {"description": "Қазақстанда арнайы техниканы жалға беру және сату"}},

    # ── PROGRAMS (education formats) ──
    26: {"en": {"title": "Online programmes", "subtitle": "Online programmes",
                "description": "Basic and advanced programmes in logistics, SCM, customs clearance and transport systems"},
         "kz": {"title": "Онлайн бағдарламалар", "subtitle": "Онлайн бағдарламалар",
                "description": "Логистика, SCM, кедендік ресімдеу және көлік жүйелері бойынша базалық және кеңейтілген бағдарламалар"}},
    27: {"en": {"title": "Workshops", "subtitle": "Intensives",
                "description": "Hands-on workshops analysing real cases. Working with documents, calculating tariffs, designing routes."},
         "kz": {"title": "Практикумдар", "subtitle": "Интенсивтер",
                "description": "Нақты кейстерді талдайтын практикалық воркшоптар. Құжаттармен жұмыс, тарифтерді есептеу, маршруттарды жобалау."}},
    28: {"en": {"title": "Corporate programmes", "subtitle": "For companies",
                "description": "Tailored training for staff in logistics, foreign-trade and procurement departments. Competency audit."},
         "kz": {"title": "Корпоративтік бағдарламалар", "subtitle": "Компанияларға",
                "description": "Логистика, СЭҚ және сатып алу бөлімшелерінің қызметкерлеріне арналған жеке оқыту бағдарламалары. Құзыреттерді аудиттеу."}},

    # ── PROJECTS (title, description, status) ──
    17: {"en": {"title": "Development of the Trans-Caspian route (TITR)", "status": "Active",
                "description": "Expert support for Middle Corridor infrastructure. Freight grew fivefold in 7 years to 4.5 million tonnes. The EU allocated €12 billion for Central Asia connectivity."},
         "kz": {"title": "Транскаспий маршрутын дамыту (ТМТМ)", "status": "Белсенді",
                "description": "Орта дәліз инфрақұрылымын сараптамалық қолдау. Жүк ағыны 7 жылда 5 есе өсіп, 4,5 млн тоннаға жетті. ЕО Орталық Азия байланысына €12 млрд бөлді."}},
    18: {"en": {"title": "Analytics of Caspian region routes", "status": "Active",
                "description": "Monitoring and analysis of freight flows through the ports of Aktau and Kuryk. Assessing the capacity and bottlenecks of Trans-Caspian transit."},
         "kz": {"title": "Каспий өңірі маршруттарының аналитикасы", "status": "Белсенді",
                "description": "Ақтау және Құрық порттары арқылы жүк ағындарын мониторингтеу және талдау. Транскаспий транзитінің өткізу қабілеті мен тар жерлерін бағалау."}},
    19: {"en": {"title": "Map of Central Asia corridors", "status": "In development",
                "description": "Visualisation and analytics of the main transport routes: rail, road, sea and multimodal corridors of the region."},
         "kz": {"title": "Орталық Азия дәліздерінің картасы", "status": "Әзірленуде",
                "description": "Негізгі көлік маршруттарын визуализациялау және талдау: өңірдің темір жол, автомобиль, теңіз және мультимодальді дәліздері."}},
    20: {"en": {"title": "Partnership with EUCA Alliance", "status": "Active",
                "description": "Cooperation with the alliance of leading Eurasian logistics companies to develop international transport corridors."},
         "kz": {"title": "EUCA Alliance-пен серіктестік", "status": "Белсенді",
                "description": "Халықаралық көлік дәліздерін дамыту үшін Еуразияның жетекші логистикалық компаниялары бірлестігімен ынтымақтастық."}},
    21: {"en": {"title": "Integration of Eurasian logistics platforms", "status": "Active",
                "description": "Creating a unified information environment for participants in the logistics chain across Central Asia and the Caucasus."},
         "kz": {"title": "Еуразия логистикалық платформаларын интеграциялау", "status": "Белсенді",
                "description": "Орталық Азия мен Кавказдағы логистикалық тізбекке қатысушылар үшін біртұтас ақпараттық орта құру."}},
    22: {"en": {"title": "Development of multimodal transport", "status": "In development",
                "description": "Designing optimal multimodal routes taking into account tariffs, delivery times and the region's infrastructure constraints."},
         "kz": {"title": "Мультимодальді тасымалдарды дамыту", "status": "Әзірленуде",
                "description": "Тарифтерді, жеткізу мерзімдерін және өңірдің инфрақұрылымдық шектеулерін ескере отырып, оңтайлы мультимодальді маршруттарды жобалау."}},
    23: {"en": {"title": "Eurasian logistics research", "status": "Active",
                "description": "A comprehensive analytical programme: trade corridors, infrastructure projects, logistics trends. Regular reports and expert reviews."},
         "kz": {"title": "Еуразия логистикасын зерттеу", "status": "Белсенді",
                "description": "Кешенді аналитикалық бағдарлама: сауда дәліздері, инфрақұрылымдық жобалар, логистикалық трендтер. Тұрақты есептер мен сараптамалық шолулар."}},
    24: {"en": {"title": "BRI Logistics Research", "status": "Active",
                "description": "Research into the impact of the Belt and Road Initiative on Central Asia's logistics infrastructure. Development scenarios to 2035."},
         "kz": {"title": "BRI Logistics Research", "status": "Белсенді",
                "description": "«Бір белдеу, бір жол» бастамасының Орталық Азия логистикалық инфрақұрылымына әсерін зерттеу. 2035 жылға дейінгі даму сценарийлері."}},
    25: {"en": {"title": "Sanctions analytics and route adaptation", "status": "Active",
                "description": "Monitoring sanctions regimes and their impact on logistics chains. Developing alternative routes and adaptation strategies."},
         "kz": {"title": "Санкциялық аналитика және маршруттарды бейімдеу", "status": "Белсенді",
                "description": "Санкциялық режимдерді және олардың логистикалық тізбектерге әсерін мониторингтеу. Балама маршруттар мен бейімделу стратегияларын әзірлеу."}},

    # ── SOLUTIONS (title, description, bullets[]) ──
    33: {"en": {"title": "Strategic sessions for companies",
                "description": "Expert support, supply chain assessment, scenario modelling and solution development to improve resilience.",
                "bullets": ["Strategic sessions and expert support",
                            "Supply chain scenario modelling",
                            "Solutions for infrastructure and international projects"]},
         "kz": {"title": "Компанияларға арналған стратегиялық сессиялар",
                "description": "Сараптамалық сүйемелдеу, жеткізу тізбегін бағалау, сценарийлерді модельдеу және орнықтылықты арттыру шешімдерін әзірлеу.",
                "bullets": ["Стратегиялық сессиялар және сараптамалық сүйемелдеу",
                            "Жеткізу тізбегі сценарийлерін модельдеу",
                            "Инфрақұрылымдық және халықаралық жобаларға арналған шешімдер"]}},
    34: {"en": {"title": "Supply chain analysis",
                "description": "A comprehensive supply chain audit — from suppliers to the end consumer. Bottlenecks, optimisation, efficiency.",
                "bullets": ["Audit of the chain and key links",
                            "Assessment of cost, lead times, reliability",
                            "Benchmarking against industry best practices",
                            "Recommendations for cost reduction"]},
         "kz": {"title": "Жеткізу тізбегін талдау",
                "description": "Жеткізушілерден соңғы тұтынушыға дейінгі жеткізу тізбегін кешенді аудиттеу. Тар жерлер, оңтайландыру, тиімділік.",
                "bullets": ["Тізбекті және негізгі буындарды аудиттеу",
                            "Құнды, мерзімдерді, сенімділікті бағалау",
                            "Сала үздік тәжірибелерімен бенчмаркинг",
                            "Шығындарды азайту бойынша ұсыныстар"]}},
    35: {"en": {"title": "Logistics risks",
                "description": "A risk map for each link: sanctions, geopolitics, infrastructure, dependence on counterparties.",
                "bullets": ["Risk map by link", "Sanctions screening", "Mitigation plans"]},
         "kz": {"title": "Логистикалық тәуекелдер",
                "description": "Әр буын бойынша тәуекелдер картасы: санкциялар, геосаясат, инфрақұрылым, контрагенттерге тәуелділік.",
                "bullets": ["Буындар бойынша тәуекелдер картасы", "Санкциялық скрининг", "Тәуекелді азайту жоспарлары"]}},
    36: {"en": {"title": "Alternative routes",
                "description": "Middle Corridor, North–South, multimodal schemes — route design and assessment.",
                "bullets": ["Route comparison", "Infrastructure readiness", "Rerouting scenarios"]},
         "kz": {"title": "Балама маршруттар",
                "description": "Орта дәліз, Солтүстік–Оңтүстік, мультимодальді схемалар — маршруттарды жобалау және бағалау.",
                "bullets": ["Маршруттарды салыстыру", "Инфрақұрылымның дайындығы", "Маршрутты қайта құру сценарийлері"]}},
    37: {"en": {"title": "Entering new markets",
                "description": "Support in entering the markets of Central Asia, the Caspian, China and Europe. From analysis to B2B connections.",
                "bullets": ["Analysis of capacity and barriers", "Regulation and customs", "B2B meetings, finding partners"]},
         "kz": {"title": "Жаңа нарықтарға шығу",
                "description": "Орталық Азия, Каспий, Қытай және Еуропа нарықтарына шығуды сүйемелдеу. Талдаудан B2B байланыстарға дейін.",
                "bullets": ["Сыйымдылық пен кедергілерді талдау", "Реттеу және кеден", "B2B кездесулер, серіктестер іздеу"]}},
}


def run():
    from apps.landing.models import SiteItem
    ok = missing = 0
    for sid, tr in TRANSLATIONS.items():
        try:
            it = SiteItem.objects.get(id=sid)
        except SiteItem.DoesNotExist:
            print("MISSING id=%s" % sid)
            missing += 1
            continue
        data = dict(it.data or {})
        i18n = dict(data.get("i18n") or {})
        for lang in ("kz", "en"):
            if lang in tr:
                block = dict(i18n.get(lang) or {})
                block.update(tr[lang])
                i18n[lang] = block
        data["i18n"] = i18n
        it.data = data
        it.save(update_fields=["data"])
        ok += 1
        print("OK id=%s [%s] %s" % (sid, it.category, it.title[:40]))
    print("DONE: %d updated, %d missing, %d total" % (ok, missing, len(TRANSLATIONS)))


run()
