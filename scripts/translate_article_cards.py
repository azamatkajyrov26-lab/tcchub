# -*- coding: utf-8 -*-
"""Populate KZ/EN translations for the analytics listing cards
(SiteItem category="article": title + description). Idempotent — merges into
SiteItem.data['i18n']. Mirrors scripts/translate_siteitems.py.

Run:  docker compose exec -T backend python manage.py shell < scripts/translate_article_cards.py
"""

CARD_TRANSLATIONS = {
    "1": {
        "en": {
            "title": "The Trans-Caspian Route: Fivefold Growth in 7 Years",
            "description": "The Trans-Caspian International Transport Route (Middle Corridor) has reached a freight volume of 4.5 million tonnes. The infrastructure investment gap is estimated at EUR 18.5 billion."
        },
        "kz": {
            "title": "Транскаспий маршруты: 7 жылда бес есе өсу",
            "description": "Транскаспий халықаралық көлік маршруты (Орта дәліз) 4.5 млн тонна жүк тасымалы көлеміне жетті. Инфрақұрылымға инвестиция тапшылығы EUR 18.5 млрд деп бағаланады."
        }
    },
    "2": {
        "en": {
            "title": "Sanctions and Rerouting: The New Map of Eurasia",
            "description": "Traffic through Suez has fallen by 90%, freight rates have risen by 80%. How pressure is shaping new trade corridors."
        },
        "kz": {
            "title": "Санкциялар мен маршруттарды қайта құру: Еуразияның жаңа картасы",
            "description": "Суэц арқылы өтетін трафик 90%-ға қысқарды, фрахт мөлшерлемелері 80%-ға өсті. Қысым қалай жаңа сауда дәліздерін қалыптастырады."
        }
    },
    "3": {
        "en": {
            "title": "The Eurasian Container Market 2025–2026",
            "description": "The China–Europe route fell by 18%, while the Middle Corridor grew by 14%. An overview of key container flows."
        },
        "kz": {
            "title": "Еуразияның контейнерлік нарығы 2025–2026",
            "description": "Қытай–Еуропа бағыты 18%-ға қысқарды, Орта дәліз 14%-ға өсті. Негізгі контейнерлік ағындарға шолу."
        }
    },
    "4": {
        "en": {
            "title": "North–South Corridor: 26.9 million tonnes",
            "description": "The INSTC posted 19% growth. Pakistan has joined, expanding the route's geography."
        },
        "kz": {
            "title": "Солтүстік–Оңтүстік дәлізі: 26.9 млн тонна",
            "description": "INSTC 19% өсім көрсетті. Пәкістан қосылып, бағыт географиясын кеңейтті."
        }
    },
    "5": {
        "en": {
            "title": "Digital Transformation of Central Asian Logistics",
            "description": "The rollout of ASYCUDAWorld, the growth of e-commerce and digital platforms are reshaping the region's logistics infrastructure."
        },
        "kz": {
            "title": "Орталық Азия логистикасының цифрлық трансформациясы",
            "description": "ASYCUDAWorld енгізілуі, электрондық сауданың және цифрлық платформалардың өсуі аймақтың логистикалық инфрақұрылымын өзгертуде."
        }
    },
    "6": {
        "en": {
            "title": "Kazakhstan: 36.9 million tonnes of transit",
            "description": "Khorgos handled 372K TEU. Kazakhstan is strengthening its position as a key transit hub of Eurasia."
        },
        "kz": {
            "title": "Қазақстан: 36.9 млн тонна транзит",
            "description": "Қорғас 372K TEU өңдеді. Қазақстан Еуразияның негізгі транзиттік хабы ретіндегі ұстанымын нығайтуда."
        }
    },
    "7": {
        "en": {
            "title": "BRI 2025: A Record $128 Billion in Contracts",
            "description": "The Belt and Road Initiative posted 81% growth. An analysis of its impact on Central Asian logistics."
        },
        "kz": {
            "title": "BRI 2025: рекордтық $128 млрд келісімшарт",
            "description": "«Бір белдеу, бір жол» бастамасы 81% өсім көрсетті. Орталық Азия логистикасына әсерін талдау."
        }
    },
    "8": {
        "en": {
            "title": "The Red Sea: How the Crisis Is Reshaping Global Routes",
            "description": "Traffic through the Suez Canal has fallen by 90%. The redistribution of cargo flows is creating opportunities for overland corridors."
        },
        "kz": {
            "title": "Қызыл теңіз: дағдарыс жаһандық маршруттарды қалай өзгертуде",
            "description": "Суэц каналы арқылы жүк ағыны 90%-ға төмендеді. Жүк ағындарын қайта бөлу құрлықтық дәліздер үшін мүмкіндіктер ашуда."
        }
    },
    "47": {
        "en": {
            "title": "Kazakhstan Between Opportunity and Overload",
            "description": "Will the country's transport system manage to reconfigure itself before Eurasia itself does? An analysis of 7 risks, 5 best and 5 worst scenarios."
        },
        "kz": {
            "title": "Қазақстан мүмкіндік пен шамадан тыс жүктеме арасында",
            "description": "Ел көлік жүйесі Еуразияның өзі қайта құрылғанға дейін қайта құрыла ала ма? 7 тәуекелге, 5 жақсы және 5 нашар сценарийге талдау."
        }
    }
}


def run():
    from apps.landing.models import SiteItem
    ok = missing = 0
    for sid, tr in CARD_TRANSLATIONS.items():
        try:
            it = SiteItem.objects.get(id=sid)
        except SiteItem.DoesNotExist:
            print("MISSING id=%s" % sid); missing += 1; continue
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
        print("OK id=%s %s" % (sid, it.title[:45]))
    print("DONE: %d updated, %d missing, %d total" % (ok, missing, len(CARD_TRANSLATIONS)))


run()
