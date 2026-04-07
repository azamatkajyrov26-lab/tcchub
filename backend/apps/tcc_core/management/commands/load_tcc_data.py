"""
Management command to load initial TCC data (countries, nodes, corridors).
Handles auto_now/auto_now_add fields properly.
"""

from django.core.management.base import BaseCommand

from apps.tcc_core.models import CorridorNode, Country, RouteNode, TradeCorridor
from apps.tcc_data.models import DataSource


COUNTRIES = [
    {"iso2": "CN", "iso3": "CHN", "name_ru": "Китай", "name_en": "China", "sanction_risk_level": "none"},
    {"iso2": "KZ", "iso3": "KAZ", "name_ru": "Казахстан", "name_en": "Kazakhstan", "sanction_risk_level": "none"},
    {"iso2": "AZ", "iso3": "AZE", "name_ru": "Азербайджан", "name_en": "Azerbaijan", "sanction_risk_level": "none"},
    {"iso2": "GE", "iso3": "GEO", "name_ru": "Грузия", "name_en": "Georgia", "sanction_risk_level": "none"},
    {"iso2": "TR", "iso3": "TUR", "name_ru": "Турция", "name_en": "Turkey", "sanction_risk_level": "none"},
    {"iso2": "RO", "iso3": "ROU", "name_ru": "Румыния", "name_en": "Romania", "sanction_risk_level": "none"},
    {"iso2": "BG", "iso3": "BGR", "name_ru": "Болгария", "name_en": "Bulgaria", "sanction_risk_level": "none"},
    {"iso2": "RU", "iso3": "RUS", "name_ru": "Россия", "name_en": "Russia", "sanction_risk_level": "critical"},
    {"iso2": "IR", "iso3": "IRN", "name_ru": "Иран", "name_en": "Iran", "sanction_risk_level": "high"},
    {"iso2": "IN", "iso3": "IND", "name_ru": "Индия", "name_en": "India", "sanction_risk_level": "none"},
    {"iso2": "UZ", "iso3": "UZB", "name_ru": "Узбекистан", "name_en": "Uzbekistan", "sanction_risk_level": "low"},
    {"iso2": "TM", "iso3": "TKM", "name_ru": "Туркменистан", "name_en": "Turkmenistan", "sanction_risk_level": "low"},
    {"iso2": "IT", "iso3": "ITA", "name_ru": "Италия", "name_en": "Italy", "sanction_risk_level": "none"},
    {"iso2": "DE", "iso3": "DEU", "name_ru": "Германия", "name_en": "Germany", "sanction_risk_level": "none"},
    {"iso2": "PL", "iso3": "POL", "name_ru": "Польша", "name_en": "Poland", "sanction_risk_level": "none"},
]

NODES = [
    # TMTM corridor
    ("Шанхай", "Shanghai", "CN", "port_sea", 31.2, 121.5, None, "Крупнейший контейнерный порт мира"),
    ("Сиань", "Xi'an", "CN", "railway", 34.3, 109.0, None, "Стартовый хаб BRI, ж/д хаб западного Китая"),
    ("Урумчи", "Urumqi", "CN", "railway", 43.8, 87.6, None, "Ворота в Центральную Азию"),
    ("Хоргос", "Khorgos", "KZ", "port_dry", 44.2, 80.3, 372000, "Крупнейший сухой порт Китай-Казахстан"),
    ("Достык", "Dostyk", "KZ", "border", 45.5, 80.4, None, "Пограничный переход Китай-Казахстан"),
    ("Алматы", "Almaty", "KZ", "hub", 43.2, 76.9, None, "Логистический хаб Центральной Азии"),
    ("Астана", "Astana", "KZ", "railway", 51.1, 71.4, None, "Столица Казахстана, HQ KTZ Express"),
    ("Атырау", "Atyrau", "KZ", "hub", 47.1, 51.9, None, "Штаб-квартира TransCaspian Cargo"),
    ("Актау", "Aktau", "KZ", "port_sea", 43.6, 51.1, None, "Крупнейший каспийский порт КЗ"),
    ("Курык", "Kuryk", "KZ", "port_sea", 42.9, 51.4, None, "Новый каспийский Ro-Ro терминал"),
    ("Баку / Алат", "Baku / Alat", "AZ", "port_sea", 40.4, 49.9, None, "Международный морской порт Баку"),
    ("Тбилиси", "Tbilisi", "GE", "railway", 41.7, 44.8, None, "Транзит BTK Railway"),
    ("Поти", "Poti", "GE", "port_sea", 42.15, 41.7, None, "Черноморский порт Грузии"),
    ("Батуми", "Batumi", "GE", "port_sea", 41.64, 41.6, None, "Черноморский порт Грузии"),
    ("Карс", "Kars", "TR", "railway", 40.6, 43.1, None, "BTK ж/д терминал Турции"),
    ("Стамбул", "Istanbul", "TR", "hub", 41.0, 29.0, None, "Крупнейший логистический хаб Турции"),
    ("Констанца", "Constanta", "RO", "port_sea", 44.2, 28.6, None, "Крупнейший черноморский порт ЕС"),
    # Northern corridor
    ("Москва", "Moscow", "RU", "hub", 55.75, 37.6, None, "Крупнейший ж/д хаб России"),
    ("Екатеринбург", "Ekaterinburg", "RU", "railway", 56.8, 60.6, None, "Ж/д узел Урала"),
    ("Новосибирск", "Novosibirsk", "RU", "railway", 55.0, 82.9, None, "Ж/д узел Сибири"),
    ("Брест", "Brest", "PL", "border", 52.1, 23.7, None, "Погранпереход РБ-ЕС"),
    # INSTC
    ("Мумбаи", "Mumbai", "IN", "port_sea", 19.1, 72.9, None, "Крупнейший порт Индии"),
    ("Бандар-Аббас", "Bandar Abbas", "IR", "port_sea", 27.2, 56.3, None, "Главный порт Ирана"),
    ("Тегеран", "Tehran", "IR", "hub", 35.7, 51.4, None, "Столица Ирана, ж/д хаб"),
    # Additional
    ("Караганда", "Karaganda", "KZ", "railway", 49.8, 73.1, None, "Ж/д узел центрального КЗ"),
    ("Шымкент", "Shymkent", "KZ", "railway", 42.3, 69.6, None, "Ж/д узел южного КЗ"),
    ("Ташкент", "Tashkent", "UZ", "hub", 41.3, 69.3, None, "Столица Узбекистана"),
    ("Туркменбаши", "Turkmenbashi", "TM", "port_sea", 40.0, 52.9, None, "Каспийский порт Туркменистана"),
    ("Мерсин", "Mersin", "TR", "port_sea", 36.8, 34.6, None, "Средиземноморский порт Турции"),
    ("Варна", "Varna", "BG", "port_sea", 43.2, 27.9, None, "Черноморский порт Болгарии"),
    ("Генуя", "Genoa", "IT", "port_sea", 44.4, 8.9, None, "Крупнейший порт Италии"),
    ("Дуйсбург", "Duisburg", "DE", "hub", 51.4, 6.8, None, "Крупнейший ж/д хаб Европы"),
    ("Варшава", "Warsaw", "PL", "hub", 52.2, 21.0, None, "Логистический хаб Польши"),
]

CORRIDORS = [
    {
        "code": "TMTM",
        "name": "Средний коридор (ТМТМ)",
        "description": "Trans-Caspian International Transport Route. Мультимодальный маршрут Китай → Казахстан → Каспий → Азербайджан → Грузия → Турция/Европа.",
        "color": "#C6A46D",
    },
    {
        "code": "NORTHERN",
        "name": "Северный коридор",
        "description": "Транссибирский маршрут Китай → Казахстан → Россия → Европа. Быстрый, но высокорисковый из-за санкций.",
        "color": "#ef4444",
    },
    {
        "code": "INSTC",
        "name": "Международный коридор Север-Юг (INSTC)",
        "description": "International North-South Transport Corridor. Индия → Иран → Азербайджан → Россия.",
        "color": "#06B6D4",
    },
    {
        "code": "BRI",
        "name": "Пояс и Путь (BRI)",
        "description": "Belt and Road Initiative — глобальная инфраструктурная инициатива Китая.",
        "color": "#22c55e",
    },
]

# (corridor_code, node_name_en, order, segment_mode, segment_distance_km)
CORRIDOR_NODES = [
    # TMTM
    ("TMTM", "Shanghai", 1, "rail", None),
    ("TMTM", "Xi'an", 2, "rail", 1500),
    ("TMTM", "Urumqi", 3, "rail", 2500),
    ("TMTM", "Khorgos", 4, "rail", 670),
    ("TMTM", "Almaty", 5, "rail", 300),
    ("TMTM", "Aktau", 6, "rail", 3000),
    ("TMTM", "Baku / Alat", 7, "ferry", 350),
    ("TMTM", "Tbilisi", 8, "rail", 550),
    ("TMTM", "Kars", 9, "rail", 260),
    ("TMTM", "Istanbul", 10, "rail", 1300),
    ("TMTM", "Constanta", 11, "sea", 600),
    # Northern
    ("NORTHERN", "Shanghai", 1, "rail", None),
    ("NORTHERN", "Urumqi", 2, "rail", 4000),
    ("NORTHERN", "Dostyk", 3, "rail", 480),
    ("NORTHERN", "Astana", 4, "rail", 1200),
    ("NORTHERN", "Moscow", 5, "rail", 3500),
    ("NORTHERN", "Brest", 6, "rail", 1100),
    # INSTC
    ("INSTC", "Mumbai", 1, "sea", None),
    ("INSTC", "Bandar Abbas", 2, "sea", 1900),
    ("INSTC", "Tehran", 3, "rail", 1350),
    ("INSTC", "Baku / Alat", 4, "rail", 700),
    ("INSTC", "Moscow", 5, "rail", 2500),
]

DATA_SOURCES = [
    {"code": "OFAC_SDN", "name": "OFAC SDN List", "source_type": "file_xml", "base_url": "https://www.treasury.gov/ofac/downloads/sdn.xml", "access_status": "available"},
    {"code": "EU_SANCTIONS", "name": "EU Consolidated Sanctions", "source_type": "file_xml", "base_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content", "access_status": "available"},
    {"code": "UN_SANCTIONS", "name": "UN Security Council Sanctions", "source_type": "file_xml", "base_url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml", "access_status": "available"},
    {"code": "WORLD_BANK", "name": "World Bank Open Data", "source_type": "api_public", "base_url": "https://api.worldbank.org/v2/", "access_status": "available"},
    {"code": "NEWS_API", "name": "NewsAPI", "source_type": "api_public", "base_url": "https://newsapi.org/v2/", "access_status": "available"},
    {"code": "KTZ_EXPRESS", "name": "KTZ Express (эмуляция)", "source_type": "emulated", "base_url": "https://ktze.kz", "access_status": "emulated"},
    {"code": "PORT_AKTAU", "name": "Порт Актау (эмуляция)", "source_type": "emulated", "base_url": "https://portaktau.kz", "access_status": "emulated"},
]


class Command(BaseCommand):
    help = "Load initial TCC data: countries, route nodes, corridors, data sources"

    def handle(self, *args, **options):
        # Countries
        for c in COUNTRIES:
            obj, created = Country.objects.update_or_create(
                iso2=c["iso2"],
                defaults=c,
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Country {c['iso2']} {c['name_ru']} — {status}")
        self.stdout.write(self.style.SUCCESS(f"Countries: {len(COUNTRIES)}"))

        # Route Nodes
        country_map = {c.iso2: c for c in Country.objects.all()}
        node_map = {}
        for name, name_en, iso2, ntype, lat, lng, cap, desc in NODES:
            country = country_map.get(iso2)
            if not country:
                self.stderr.write(f"  Country {iso2} not found for node {name}")
                continue
            obj, created = RouteNode.objects.update_or_create(
                name_en=name_en,
                country=country,
                defaults={
                    "name": name,
                    "node_type": ntype,
                    "lat": lat,
                    "lng": lng,
                    "capacity_teu_year": cap,
                    "description": desc,
                },
            )
            node_map[name_en] = obj
            status = "created" if created else "updated"
            self.stdout.write(f"  Node {name_en} — {status}")
        self.stdout.write(self.style.SUCCESS(f"Nodes: {len(NODES)}"))

        # Corridors
        corridor_map = {}
        for c in CORRIDORS:
            obj, created = TradeCorridor.objects.update_or_create(
                code=c["code"],
                defaults={
                    "name": c["name"],
                    "description": c["description"],
                    "color": c["color"],
                },
            )
            corridor_map[c["code"]] = obj
            status = "created" if created else "updated"
            self.stdout.write(f"  Corridor {c['code']} — {status}")
        self.stdout.write(self.style.SUCCESS(f"Corridors: {len(CORRIDORS)}"))

        # Corridor Nodes
        cn_count = 0
        for code, node_en, order, mode, dist in CORRIDOR_NODES:
            corridor = corridor_map.get(code)
            node = node_map.get(node_en)
            if not corridor or not node:
                self.stderr.write(f"  Missing corridor={code} or node={node_en}")
                continue
            obj, created = CorridorNode.objects.update_or_create(
                corridor=corridor,
                node=node,
                defaults={
                    "order": order,
                    "segment_mode": mode,
                    "segment_distance_km": dist,
                },
            )
            cn_count += 1
        self.stdout.write(self.style.SUCCESS(f"Corridor nodes: {cn_count}"))

        # Data Sources
        for ds in DATA_SOURCES:
            obj, created = DataSource.objects.update_or_create(
                code=ds["code"],
                defaults=ds,
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  DataSource {ds['code']} — {status}")
        self.stdout.write(self.style.SUCCESS(f"Data sources: {len(DATA_SOURCES)}"))

        self.stdout.write(self.style.SUCCESS("\nAll TCC initial data loaded!"))
