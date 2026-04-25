import json
import logging
import urllib.request
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import CustomUser
from apps.landing.models import (
    Advantage,
    ContactInfo,
    ContactSubmission,
    ContentBlock,
    HeroSection,
    Metric,
    Partner,
    Testimonial,
)

_tg_logger = logging.getLogger("tcchub.telegram")


def _tg_request(method, payload):
    """Low-level Telegram API call."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    if not token:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/{method}"
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        _tg_logger.warning("telegram api failed (%s): %s", method, e)


def _notify_telegram(text, reply_markup=None):
    """Send notification to all admin chat IDs."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    if not token:
        return
    admin_ids_raw = getattr(settings, "TELEGRAM_ADMIN_IDS", "") or getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
    admin_ids = [i.strip() for i in str(admin_ids_raw).split(",") if i.strip()]
    for chat_id in admin_ids:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        _tg_request("sendMessage", payload)


def _tg_send(chat_id, text, reply_markup=None):
    """Send message to specific chat_id."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    _tg_request("sendMessage", payload)


def _tg_answer_callback(callback_query_id, text=""):
    _tg_request("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text})


# ── Bot menu keyboards ──────────────────────────────────────────
_MAIN_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📋 Последние заявки", "callback_data": "leads_recent"},
            {"text": "📊 Статистика", "callback_data": "stats"},
        ],
        [
            {"text": "🌐 Открыть сайт", "url": "http://tc-cargo.kz"},
            {"text": "⚙️ Админ-панель", "url": "http://tc-cargo.kz/admin/"},
        ],
        [
            {"text": "📬 Контакты страница", "url": "http://tc-cargo.kz/contacts/"},
            {"text": "📰 Аналитика", "url": "http://tc-cargo.kz/analytics/"},
        ],
    ]
}

_ADMIN_IDS_CACHE = None

def _get_admin_ids():
    global _ADMIN_IDS_CACHE
    if _ADMIN_IDS_CACHE is None:
        raw = getattr(settings, "TELEGRAM_ADMIN_IDS", "") or getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
        _ADMIN_IDS_CACHE = set(str(i).strip() for i in str(raw).split(",") if i.strip())
    return _ADMIN_IDS_CACHE


# ──────────────────────────────────────────────
# Landing
# ──────────────────────────────────────────────

def landing_view(request):
    hero = HeroSection.objects.filter(is_active=True).first()
    metrics = Metric.objects.all()[:6]
    partners = Partner.objects.all()
    testimonials = list(Testimonial.objects.all())
    advantages = Advantage.objects.all()
    contact = ContactInfo.objects.first()
    content_blocks = ContentBlock.objects.filter(is_visible=True)

    return render(request, "site/index.html", {
        "active_page": "home",
        "hero": hero,
        "metrics": metrics,
        "partners": partners,
        "testimonials": testimonials,
        "advantages": advantages,
        "contact": contact,
        "content_blocks": content_blocks,
        "current_year": datetime.now().year,
    })


# ──────────────────────────────────────────────
# Public Pages
# ──────────────────────────────────────────────

def about_view(request):
    return render(request, "site/about.html", {
        "active_page": "about",
        "experts": _site_items("expert").order_by("order"),
    })


def site_analytics_view(request):
    from apps.landing.models import SiteItem
    articles = SiteItem.objects.filter(category="article", is_published=True).order_by("order")
    return render(request, "site/analytics.html", {
        "active_page": "analytics",
        "articles": articles,
    })




# ── News categorization by keywords ──────────────────────────
_NEWS_CATEGORIES = [
    {
        "code": "corridor",
        "label": "Средний коридор",
        "color": "#C6A46D",
        "bg": "rgba(198,164,109,.12)",
        "keywords": ["middle corridor", "tmtm", "тмтм", "trans-caspian",
                     "транскаспий", "caspian", "каспи", "titr", "bri",
                     "silk road", "шёлковый", "khorgos", "хоргос",
                     "aktau", "актау", "kuryk", "курык", "btk", "bacu",
                     "baku", "баку", "atyrau", "атырау"],
    },
    {
        "code": "rail",
        "label": "Железные дороги",
        "color": "#06B6D4",
        "bg": "rgba(6,182,212,.12)",
        "keywords": ["railway", "railroad", "rail ", "ж/д", "железнодорожн",
                     "ktz", "ktze", "ktj", "adya", "ady", "georgian railway",
                     "btk", "train", "поезд", "локомотив", "вагон",
                     "freight rail", "intermodal"],
    },
    {
        "code": "shipping",
        "label": "Порты и суда",
        "color": "#3B82F6",
        "bg": "rgba(59,130,246,.12)",
        "keywords": ["port ", "shipping", "vessel", "container ship",
                     "maritime", "seaport", "порт", "судно", "суда",
                     "контейнер", "ferry", "паром", "суэц", "suez",
                     "gcaptain", "tanker", "bulk carrier", "sea route"],
    },
    {
        "code": "sanctions",
        "label": "Санкции и риски",
        "color": "#EF4444",
        "bg": "rgba(239,68,68,.12)",
        "keywords": ["sanction", "санкци", "risk", "риск", "ofac",
                     "embargo", "restriction", "compliance", "blacklist",
                     "geopolit", "геополит", "conflict", "конфликт",
                     "war ", "война", "tariff", "тариф"],
    },
    {
        "code": "trade",
        "label": "Торговля",
        "color": "#10B981",
        "bg": "rgba(16,185,129,.12)",
        "keywords": ["trade", "торговл", "export", "import", "экспорт",
                     "импорт", "customs", "таможн", "cargo volume",
                     "freight volume", "teu", "грузооборот", "товарооборот",
                     "supply chain", "цепочк", "logistics hub"],
    },
    {
        "code": "analytics",
        "label": "Аналитика",
        "color": "#8B5CF6",
        "bg": "rgba(139,92,246,.12)",
        "keywords": ["analysis", "research", "report", "forecast",
                     "аналитик", "исследован", "прогноз", "отчёт",
                     "study", "index", "индекс", "statistics", "статистик",
                     "outlook", "review", "обзор", "adb", "world bank"],
    },
]

_CAT_LOOKUP = {c["code"]: c for c in _NEWS_CATEGORIES}


def _categorize_news(title, content=""):
    """Return category code based on title+content keywords."""
    text = (title + " " + (content or "")).lower()
    for cat in _NEWS_CATEGORIES:
        if any(kw in text for kw in cat["keywords"]):
            return cat["code"]
    return "trade"  # default


@login_required
def news_feed_view(request):
    """News feed page — login required."""
    from apps.tcc_data.models import NewsItem, DataSource
    source_code = request.GET.get("source", "")
    category_code = request.GET.get("cat", "")
    search = request.GET.get("q", "").strip()

    qs = NewsItem.objects.select_related("source").order_by("-published_at")
    if source_code:
        qs = qs.filter(source__code=source_code)
    if search:
        qs = qs.filter(title__icontains=search)

    # Fetch and categorize (use public attr — Django templates block _underscore attrs)
    all_items = list(qs[:300])
    for item in all_items:
        item.news_category = _categorize_news(item.title, item.content)

    # Filter by category if selected
    if category_code:
        all_items = [i for i in all_items if i.news_category == category_code]

    news_items = all_items[:60]

    sources = DataSource.objects.filter(
        news_items__isnull=False
    ).distinct().order_by("name")

    # Count per category for tab badges
    cat_counts = {}
    for item in all_items:
        cat_counts[item.news_category] = cat_counts.get(item.news_category, 0) + 1

    categories_with_counts = [
        {**cat, "count": cat_counts.get(cat["code"], 0)}
        for cat in _NEWS_CATEGORIES
    ]

    return render(request, "site/news_feed.html", {
        "active_page": "news",
        "news_items": news_items,
        "sources": sources,
        "current_source": source_code,
        "current_category": category_code,
        "search": search,
        "categories": categories_with_counts,
        "cat_lookup": _CAT_LOOKUP,
        "total_count": len(all_items),
    })


@login_required
@csrf_exempt
@require_POST
def news_refresh_view(request):
    """Trigger RSS fetch + translation tasks, return task IDs."""
    from apps.tcc_data.tasks import fetch_rss_news, translate_news_to_russian
    t1 = fetch_rss_news.delay()
    t2 = translate_news_to_russian.delay()
    return JsonResponse({"ok": True, "fetch_id": str(t1.id), "translate_id": str(t2.id)})


@login_required
def news_status_view(request):
    """Return current news stats for progress polling."""
    from apps.tcc_data.models import NewsItem
    total = NewsItem.objects.count()
    translated = NewsItem.objects.filter(ai_processed=True).count()
    pending = total - translated
    return JsonResponse({
        "total": total,
        "translated": translated,
        "pending": pending,
        "pct": round(translated / total * 100) if total else 0,
    })


@login_required
def news_analysis_view(request):
    """AI Analysis Report page — login required."""
    from apps.tcc_data.models import NewsItem, DataSource
    from django.db.models import Count, Avg, Q

    total = NewsItem.objects.count()
    analyzed = NewsItem.objects.filter(groq_processed=True, groq_score__isnull=False).count()
    pending = NewsItem.objects.filter(groq_processed=False).count()
    avg_score = NewsItem.objects.filter(groq_score__isnull=False).aggregate(
        Avg('groq_score'))['groq_score__avg'] or 0

    # Score buckets
    critical = NewsItem.objects.filter(groq_score__gte=8).count()
    high = NewsItem.objects.filter(groq_score__gte=6, groq_score__lt=8).count()
    medium = NewsItem.objects.filter(groq_score__gte=4, groq_score__lt=6).count()
    low = NewsItem.objects.filter(groq_score__gt=0, groq_score__lt=4).count()
    irrelevant = NewsItem.objects.filter(groq_score=0).count()

    # Impact types
    impact_types = list(
        NewsItem.objects.filter(groq_impact_type__gt='', groq_processed=True)
        .values('groq_impact_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Top corridor-relevant articles
    top_articles = NewsItem.objects.filter(
        groq_score__gte=6
    ).select_related('source').order_by('-groq_score', '-published_at')[:15]

    # Sources stats
    sources_stats = list(
        NewsItem.objects.filter(groq_processed=True)
        .values('source__name', 'source__code')
        .annotate(count=Count('id'), avg_score=Avg('groq_score'))
        .order_by('-avg_score')[:10]
    )

    # Recent analysis (last 24h)
    from django.utils import timezone
    from datetime import timedelta
    recent = NewsItem.objects.filter(
        groq_processed=True,
        published_at__gte=timezone.now() - timedelta(hours=24)
    ).count()

    return render(request, "site/news_analysis.html", {
        "active_page": "news",
        "total": total,
        "analyzed": analyzed,
        "pending": pending,
        "avg_score": round(avg_score, 1),
        "pct_analyzed": round(analyzed / total * 100) if total else 0,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "irrelevant": irrelevant,
        "impact_types": impact_types,
        "top_articles": top_articles,
        "sources_stats": sources_stats,
        "recent": recent,
    })


REPORT_TYPES = {
    "digest": {
        "name": "Еженедельный дайджест",
        "desc": "Краткий обзор ключевых событий за неделю. Формат McKinsey Pyramid: Ситуация → Проблема → Вывод.",
        "days": 7,
        "style": "digest",
        "standard": "McKinsey Pyramid Principle",
    },
    "analytical": {
        "name": "Аналитический отчёт",
        "desc": "Полный анализ за месяц по стандарту ADB/World Bank: Executive Summary + Corridor Analysis + Risk Matrix.",
        "days": 30,
        "style": "analytical",
        "standard": "ADB Central Asia Transport Report Format",
    },
    "event": {
        "name": "Событийный отчёт",
        "desc": "Анализ конкретного события и его влияния на маршрут. Формат: Факт → Влияние → Рекомендации.",
        "days": 3,
        "style": "event",
        "standard": "OECD Policy Brief Format",
    },
    "investment": {
        "name": "Инвестиционный брифинг",
        "desc": "Квартальный обзор для инвесторов и партнёров. Стандарт SCOR + World Bank LPI методология.",
        "days": 90,
        "style": "investment",
        "standard": "World Bank / IFC Investment Brief",
    },
}


def report_generate_view(request):
    """Report generation page — select type and generate."""
    from apps.tcc_data.models import NewsItem
    from django.db.models import Count, Avg

    report_type = request.GET.get("type", "")
    selected = REPORT_TYPES.get(report_type)

    import json as _json
    context = {
        "active_page": "news",
        "report_types": REPORT_TYPES,
        "report_types_json": _json.dumps({k: {"name": v["name"], "days": v["days"], "standard": v["standard"], "desc": v["desc"]} for k, v in REPORT_TYPES.items()}),
        "selected_type": report_type,
        "selected": selected,
        "total_news": NewsItem.objects.count(),
        "analyzed_news": NewsItem.objects.filter(groq_processed=True).count(),
        "sources_count": 12,
    }

    if report_type and selected and request.method == "POST":
        # Generate report with Groq
        report_data = _generate_report(report_type, selected)
        context["report"] = report_data
        context["generating"] = False
    elif report_type and selected and request.method == "GET" and request.GET.get("generate"):
        report_data = _generate_report(report_type, selected)
        context["report"] = report_data

    return render(request, "site/report_generate.html", context)


def _generate_report(report_type, config):
    """Generate report content using Groq + DB data."""
    import os, json, requests as _req
    from apps.tcc_data.models import NewsItem
    from django.db.models import Count, Avg, Q
    from django.utils import timezone
    from datetime import timedelta

    groq_key = os.getenv("GROQ_API_KEY", "")
    days = config["days"]
    since = timezone.now() - timedelta(days=days)

    # Gather data
    all_items = NewsItem.objects.filter(
        groq_processed=True, groq_score__isnull=False,
        published_at__gte=since
    ).select_related("source").order_by("-groq_score")

    total_period = NewsItem.objects.filter(published_at__gte=since).count()
    analyzed = all_items.count()
    avg_score = all_items.aggregate(Avg("groq_score"))["groq_score__avg"] or 0
    critical = all_items.filter(groq_score__gte=8)
    high = all_items.filter(groq_score__gte=6, groq_score__lt=8)
    medium = all_items.filter(groq_score__gte=4, groq_score__lt=6)

    impact_types = list(
        all_items.values("groq_impact_type").annotate(c=Count("id")).order_by("-c")[:6]
    )

    top_articles = list(all_items.filter(groq_score__gte=5)[:10].values(
        "title", "groq_score", "groq_impact_type",
        "groq_summary_ru", "groq_affected_nodes",
        "url", "published_at", "source__name"
    ))

    # Prepare headlines for Groq
    headlines = "\n".join([
        f"[{a['groq_score']}/10] {a['title']} ({a['groq_impact_type'] or 'прочее'})"
        for a in top_articles[:15]
    ])

    # Groq prompts per report type
    # TITR/Middle Corridor 2024 benchmarks (World Bank, ADB, TITR Association data)
    CORRIDOR_CONTEXT = """
СПРАВКА — Транскаспийский Средний коридор (ТМТМ/TITR), актуальные данные 2024-2025:
• Объём груза: 4.5 млн тонн в 2024 г. (+62% г/г); контейнеры: 50 500 TEU за 11 мес 2024
• Транзитное время: 18-23 дня (Китай→Европа); цель TITR: 14-18 дней
• Пропускная способность: ~6 млн тонн/год при текущей инфраструктуре; цель 2030: 10 млн тонн
• Ключевые узлы: Хоргос/Достык (граница КЗ-КНР) → Алматы → Актау/Курык (порты КЗ) → паром Каспий → Баку (Алат) → Тбилиси → Карс → Стамбул/Поти
• Конкуренты: Северный коридор (через РФ, санкции 2022+), Южный (через ИРН, санкции), морской через Суэц
• LPI 2023: Казахстан 79-е место, Азербайджан 97-е, Грузия 61-е (из 139 стран)
• ADB CAREC CPMM 4 индикатора: время на КПП, стоимость на КПП, стоимость на сегменте ($/ткм), скорость (км/ч)
• Стандарт анализа: UNESCAP TCD (Time-Cost-Distance), ADB CAREC CPMM, World Bank LPI методология
"""

    prompts = {
        "digest": f"""Ты — старший аналитик Транскаспийского коридора (ТМТМ). Напиши ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ строго по формату McKinsey Pyramid Principle.

{CORRIDOR_CONTEXT}

ДАННЫЕ ПЕРИОДА (последние {days} дней):
• Проанализировано статей ИИ: {analyzed}
• Средний балл влияния на коридор: {avg_score:.1f}/10
• Критичных событий (≥8/10): {critical.count()}
• Событий высокого приоритета (6-8/10): {high.count()}

ТОП СОБЫТИЙ по влиянию на маршрут:
{headlines}

Сформируй JSON строго по структуре McKinsey Pyramid (MECE principle):
{{
  "executive_summary": "2-3 предложения — один ключевой тезис недели с конкретными данными",
  "situation": "Текущее состояние ТМТМ — объём трафика, транзитное время, ценообразование. Сравни с бенчмарком (18-23 дня, 4.5 млн т/год). 3-4 предложения.",
  "complication": "Что изменилось или угрожает изменить ситуацию — конкретные события из новостей. 2-3 предложения.",
  "key_insight": "Ключевой вывод аналитика — что это означает для бизнеса и маршрута. 1-2 предложения.",
  "risk_level": "ВЫСОКИЙ/СРЕДНИЙ/НИЗКИЙ",
  "risk_rationale": "Конкретное обоснование уровня риска с привязкой к событиям. 2 предложения.",
  "top_events": [
    "Событие 1: [источник] — конкретный факт и его влияние на коридор",
    "Событие 2: [источник] — конкретный факт и его влияние на коридор",
    "Событие 3: [источник] — конкретный факт и его влияние на коридор"
  ],
  "recommendation": "Конкретные действия для грузоотправителей, логистов, инвесторов прямо сейчас. 2-3 предложения.",
  "kpi_watch": ["Индикатор для мониторинга 1", "Индикатор для мониторинга 2"]
}}""",

        "analytical": f"""Ты — старший аналитик LogiCorridor™. Напиши АНАЛИТИЧЕСКИЙ ОТЧЁТ по стандарту ADB CAREC CPMM + World Bank Corridor Report.

{CORRIDOR_CONTEXT}

ДАННЫЕ ПЕРИОДА (последние {days} дней):
• Всего статей за период: {total_period}
• Проанализировано ИИ: {analyzed} (UNESCAP TCD методология, шкала 0-10)
• Средний балл влияния на коридор: {avg_score:.1f}/10
• Распределение: критично≥8: {critical.count()}, высокий 6-8: {high.count()}, средний 4-6: {medium.count()}

КЛЮЧЕВЫЕ СОБЫТИЯ (ранжированы по ADB CAREC приоритету):
{headlines}

Сформируй JSON по стандарту ADB/World Bank Middle Corridor Report:
{{
  "executive_summary": "4-5 предложений: ключевые выводы периода с конкретными данными и сравнением с бенчмарком ТМТМ",
  "corridor_status": "НОРМАЛЬНЫЙ/НАПРЯЖЁННЫЙ/КРИТИЧЕСКИЙ",
  "corridor_assessment": "Оценка 4 индикаторов ADB CPMM: (1) транзитное время vs 18-23д норма, (2) стоимость перевозки vs конкуренты, (3) надёжность расписания, (4) доступность ёмкости. 5-6 предложений.",
  "infrastructure_findings": "Состояние ключевых узлов: Хоргос, Актау/Курык, Алат (Баку), Поти/Батуми, грузинские ж/д. Что изменилось за период. 4-5 предложений.",
  "trade_flow_impact": "Влияние новостей на объёмы и маршрутизацию грузов. Сравни с Северным/Южным коридором. 3-4 предложения.",
  "lpi_dimension_assessment": {{
    "customs": "Оценка таможенных процедур КЗ/АЗ/ГЕ на основе новостей",
    "infrastructure": "Изменения в инфраструктуре за период",
    "shipments": "Доступность и конкурентность услуг",
    "logistics_quality": "Качество операторов и отслеживание грузов",
    "timeliness": "Выполнение расписания и предсказуемость"
  }},
  "risk_matrix": [
    {{"risk": "Конкретный риск из новостей", "category": "геополитика/инфраструктура/тариф/регуляторный/операционный", "probability": "ВЫСОКАЯ/СРЕДНЯЯ/НИЗКАЯ", "impact": "ВЫСОКИЙ/СРЕДНИЙ/НИЗКИЙ", "description": "2-3 предложения о природе риска и механизме влияния на коридор", "mitigation": "Действие для снижения риска"}},
    {{"risk": "Риск 2", "category": "...", "probability": "СРЕДНЯЯ", "impact": "ВЫСОКИЙ", "description": "...", "mitigation": "..."}}
  ],
  "key_findings": [
    "Находка 1: конкретный факт с данными",
    "Находка 2: конкретный факт с данными",
    "Находка 3: конкретный факт с данными",
    "Находка 4: конкретный факт с данными"
  ],
  "policy_recommendations": [
    "Краткосрочная рекомендация (0-3 месяца): конкретное действие",
    "Среднесрочная рекомендация (3-12 месяцев): конкретное действие",
    "Долгосрочная рекомендация (1-3 года): конкретное действие"
  ],
  "outlook": "Прогноз на следующие 30 дней с указанием триггеров изменения сценария. 3-4 предложения.",
  "data_quality_note": "Методологическое замечание: источники, ограничения, уровень доверия к данным"
}}""",

        "event": f"""Ты — аналитик кризисных ситуаций. Напиши СОБЫТИЙНЫЙ АНАЛИЗ по формату OECD Policy Brief + UN-OHRLLS Corridor Report.

{CORRIDOR_CONTEXT}

ДАННЫЕ (последние {days} дня — острая фаза):
• Событий проанализировано ИИ: {analyzed}
• Критичных (≥8/10): {critical.count()}

НАИБОЛЕЕ КРИТИЧНЫЕ СОБЫТИЯ:
{headlines}

Сформируй JSON по стандарту OECD Policy Brief:
{{
  "key_event_title": "Точное название главного события периода",
  "key_event_summary": "Что произошло: факты, даты, стороны. 4-5 предложений.",
  "corridor_nodes_affected": ["Список конкретных узлов: Актау, Баку, Хоргос, паром, ж/д"],
  "immediate_impact": "Немедленное влияние на транзит (24-72 часа): задержки, объёмы, тарифы. 3-4 предложения.",
  "tcd_impact": {{
    "time_delta": "Изменение транзитного времени в днях (+/-X дней от нормы 18-23 дня)",
    "cost_delta": "Изменение стоимости перевозки (+/-X% от нормы)",
    "reliability_delta": "Изменение надёжности расписания"
  }},
  "secondary_effects": "Вторичные эффекты через 1-4 недели: перераспределение грузов, маршрутизация. 3 предложения.",
  "route_diversion_risk": "Вероятность переключения грузов на Северный или Южный коридор: ВЫСОКАЯ/СРЕДНЯЯ/НИЗКАЯ. Обоснование.",
  "stakeholder_implications": {{
    "грузоотправители": "Конкретное влияние и рекомендуемые действия",
    "перевозчики_операторы": "Конкретное влияние и рекомендуемые действия",
    "государства_транзита": "Конкретное влияние и рекомендуемые действия",
    "инвесторы": "Конкретное влияние и рекомендуемые действия"
  }},
  "urgent_actions": [
    "Действие 1 (сделать в течение 48 часов)",
    "Действие 2 (сделать в течение 1 недели)"
  ],
  "monitoring_indicators": [
    "Что отслеживать ежедневно",
    "Что отслеживать еженедельно",
    "Триггер эскалации до следующего уровня"
  ],
  "precedent_analysis": "Как аналогичные события влияли на ТМТМ в прошлом. 2 предложения."
}}""",

        "investment": f"""Ты — партнёр инвестиционного консалтинга. Напиши ИНВЕСТИЦИОННЫЙ БРИФИНГ по стандарту World Bank / IFC + McKinsey Strategic Analysis.

{CORRIDOR_CONTEXT}

ДАННЫЕ ПЕРИОДА (квартал, {days} дней):
• Статей проанализировано: {total_period}
• Средний риск-балл коридора: {avg_score:.1f}/10
• Событий влияющих на инвестиционный климат: {critical.count() + high.count()}

КЛЮЧЕВЫЕ СОБЫТИЯ ДЛЯ ИНВЕСТОРОВ:
{headlines}

Сформируй JSON по стандарту World Bank/IFC Investment Brief:
{{
  "executive_brief": "3-4 предложения: инвестиционный тезис периода. Подкреплён конкретными данными о росте объёмов (+62% 2024), транзитном времени, ёмкости.",
  "corridor_investment_climate": "БЛАГОПРИЯТНЫЙ/НЕЙТРАЛЬНЫЙ/НЕБЛАГОПРИЯТНЫЙ",
  "climate_rationale": "4-5 предложений: почему такой климат. Факты о геополитике, инфраструктуре, регуляторике, рыночной динамике.",
  "market_sizing": {{
    "current_volume": "4.5 млн тонн/год (2024) — оценка текущего рынка",
    "addressable_market": "EU-China + EU-ЦА торговля, потенциально маршрутизируемая через ТМТМ",
    "growth_scenario": "Консервативный/Базовый/Оптимистичный прогнозы объёмов к 2027/2030"
  }},
  "opportunities": [
    "Возможность 1: конкретная ниша с оценкой рынка",
    "Возможность 2: конкретная ниша с оценкой рынка",
    "Возможность 3: конкретная ниша с оценкой рынка"
  ],
  "investment_barriers": [
    "Барьер 1: конкретный с оценкой затрат на преодоление",
    "Барьер 2: конкретный с оценкой затрат на преодоление"
  ],
  "risk_matrix_for_investors": [
    {{"risk": "Риск 1", "probability": "ВЫСОКАЯ/СРЕДНЯЯ/НИЗКАЯ", "impact": "ВЫСОКИЙ/СРЕДНИЙ/НИЗКИЙ", "mitigation": "Инструмент хеджирования"}},
    {{"risk": "Риск 2", "probability": "СРЕДНЯЯ", "impact": "ВЫСОКИЙ", "mitigation": "..."}}
  ],
  "infrastructure_gaps_and_capex": [
    "Инфраструктурная потребность 1 с оценкой capex ($ млн)",
    "Инфраструктурная потребность 2 с оценкой capex ($ млн)"
  ],
  "financial_metrics": {{
    "transit_volume_trend": "РОСТ/СТАБИЛЬНО/СНИЖЕНИЕ + темп",
    "freight_rate_trend": "РОСТ/СТАБИЛЬНО/СНИЖЕНИЕ + темп",
    "transit_time_trend": "УЛУЧШЕНИЕ/СТАБИЛЬНО/УХУДШЕНИЕ + дней",
    "infrastructure_utilization": "Загрузка ключевых мощностей % от capacity"
  }},
  "strategic_recommendations": [
    "Quick win (0-6 месяцев): конкретное инвестиционное действие",
    "Среднесрочно (6-24 месяца): конкретное инвестиционное действие",
    "Долгосрочно (2-5 лет): конкретное инвестиционное действие"
  ],
  "due_diligence_checklist": ["Что проверить перед инвестицией 1", "Что проверить 2", "Что проверить 3"],
  "disclaimer": "Настоящий брифинг подготовлен исключительно в информационных целях на основе публично доступных данных и анализа ИИ. Не является офертой или инвестиционной рекомендацией. © TransCaspian Cargo Analytics."
}}""",
    }

    # Call Groq with higher token limit for full reports
    groq_result = {}
    if groq_key and report_type in prompts:
        try:
            resp = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompts[report_type]}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.35,
                    "max_tokens": 2500,
                },
                timeout=45,
            )
            if resp.status_code == 200:
                groq_result = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            groq_result = {"error": str(e)}

    # Normalize groq_result — fill all possible keys so templates don't crash
    _all_keys = [
        "executive_summary", "executive_brief", "situation", "complication",
        "key_insight", "risk_level", "corridor_status", "corridor_investment_climate",
        "risk_rationale", "climate_rationale", "top_events", "recommendation",
        "kpi_watch", "corridor_assessment", "infrastructure_findings", "trade_flow_impact",
        "lpi_dimension_assessment", "risk_matrix", "key_findings", "policy_recommendations",
        "outlook", "data_quality_note", "key_event_title", "key_event_summary",
        "corridor_nodes_affected", "immediate_impact", "tcd_impact", "secondary_effects",
        "route_diversion_risk", "stakeholder_implications", "urgent_actions",
        "monitoring_indicators", "precedent_analysis", "market_sizing", "opportunities",
        "investment_barriers", "risks_for_investors", "infrastructure_gaps_and_capex",
        "financial_metrics", "strategic_recommendations", "due_diligence_checklist",
        "disclaimer", "affected_segments", "comparison",
    ]
    for k in _all_keys:
        if k not in groq_result:
            groq_result[k] = [] if k in ["top_events","key_findings","policy_recommendations",
                "risk_matrix","opportunities","urgent_actions","monitoring_indicators",
                "corridor_nodes_affected","affected_segments","strategic_recommendations",
                "due_diligence_checklist","infrastructure_gaps_and_capex","kpi_watch",
                "investment_barriers","risks_for_investors"] else ""

    return {
        "type": report_type,
        "config": config,
        "generated_at": timezone.now(),
        "period_days": days,
        "stats": {
            "total_period": total_period,
            "analyzed": analyzed,
            "avg_score": round(avg_score, 1),
            "critical_count": critical.count(),
            "high_count": high.count(),
            "medium_count": medium.count(),
        },
        "impact_types": impact_types,
        "top_articles": top_articles,
        "groq": groq_result,
        "has_ai": bool(groq_result and "error" not in groq_result),
    }


@require_POST
@login_required
def report_publish_view(request):
    """Save generated report to user's cabinet. Admin can publish to catalog."""
    from apps.tcc_reports.models import Report, ReportTemplate, ReportSection
    from django.utils import timezone
    import json as _json

    report_type = request.POST.get("report_type", "digest")
    config = REPORT_TYPES.get(report_type, REPORT_TYPES["digest"])

    # Generate the report data
    report_data = _generate_report(report_type, config)

    # Get or create template
    template, _ = ReportTemplate.objects.get_or_create(
        code=report_type,
        defaults={
            "name": config["name"],
            "description": config["desc"],
        },
    )

    # Build content from AI analysis
    summary = ""
    findings = []
    recommendations = []
    groq = report_data.get("groq", {})
    if groq:
        summary = groq.get("executive_summary", "")
        findings = groq.get("top_events", [])
        recommendations = groq.get("recommendations", [])

    report = Report.objects.create(
        template=template,
        title=f"{config['name']} — {timezone.now().strftime('%d.%m.%Y')}",
        subtitle=config["standard"],
        status="draft",
        created_by=request.user,
        executive_summary=summary,
        key_findings=findings,
        recommendations=recommendations,
        is_free_preview=True,
        preview_text=summary,
    )

    # Save full AI analysis as section
    if groq:
        ReportSection.objects.create(
            report=report,
            title="Анализ AI",
            section_type="text",
            content=_json.dumps(groq, ensure_ascii=False),
            order=1,
        )

    # Save stats as section
    stats = report_data.get("stats", {})
    if stats:
        ReportSection.objects.create(
            report=report,
            title="Статистика",
            section_type="text",
            content=_json.dumps(stats, ensure_ascii=False),
            order=0,
        )

    return redirect("dashboard_my_reports")


def report_detail_view_custom(request, report_id):
    """Placeholder — redirect to generate."""
    return redirect("report_generate")


def report_pdf_view(request, report_id):
    """Render print-optimized HTML page — user prints to PDF via browser."""
    report_type = request.GET.get("type", "digest")
    selected = REPORT_TYPES.get(report_type, REPORT_TYPES["digest"])
    report_data = _generate_report(report_type, selected)
    return render(request, "site/report_pdf.html", {"report": report_data})


def solutions_view(request):
    return render(request, "site/solutions.html", {
        "active_page": "solutions",
        "solutions_list": _site_items("solution").order_by("order"),
    })


def education_view(request):
    return render(request, "site/education.html", {
        "active_page": "education",
        "programs": _site_items("program").order_by("order"),
    })


def projects_view(request):
    return render(request, "site/projects.html", {
        "active_page": "projects",
        "projects_mc": _site_items("project", "middle_corridor").order_by("order"),
        "projects_intl": _site_items("project", "international").order_by("order"),
        "projects_research": _site_items("project", "research").order_by("order"),
    })


def site_media_view(request):
    from apps.landing.models import SiteNews
    news = SiteNews.objects.filter(is_published=True)
    return render(request, "site/media.html", {
        "active_page": "media",
        "news_items": news,
    })


def _site_items(category, subcategory=None):
    from apps.landing.models import SiteItem
    qs = SiteItem.objects.filter(category=category, is_published=True)
    if subcategory is not None:
        qs = qs.filter(subcategory=subcategory)
    return qs


def site_partners_view(request):
    return render(request, "site/partners.html", {
        "active_page": "partners",
        "partners_intl": _site_items("partner", "international").order_by("order"),
        "partners_edu": _site_items("partner", "education").order_by("order"),
    })


def contacts_view(request):
    return render(request, "site/contacts.html", {"active_page": "contacts"})


@csrf_exempt
@require_POST
def contact_submit_view(request):
    """AJAX endpoint: save contact form + notify via Telegram."""
    name = (request.POST.get("name") or "").strip()[:200]
    phone = (request.POST.get("phone") or "").strip()[:50]
    email = (request.POST.get("email") or "").strip()[:254]
    message = (request.POST.get("message") or "").strip()[:3000]
    if not name:
        return JsonResponse({"ok": False, "error": "Укажите имя"}, status=400)
    sub = ContactSubmission.objects.create(
        name=name, phone=phone, email=email, message=message, source="contacts",
    )
    tg_text = (
        f"<b>Новая заявка с сайта</b>\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Телефон:</b> {phone or '—'}\n"
        f"<b>Email:</b> {email or '—'}\n"
        f"<b>Сообщение:</b> {message or '—'}\n\n"
        f"#{sub.pk} · {sub.created_at:%d.%m.%Y %H:%M}"
    )
    lead_keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Обработано", "callback_data": f"lead_done_{sub.pk}"},
            {"text": "🌐 Сайт", "url": "http://tc-cargo.kz"},
        ]]
    }
    _notify_telegram(tg_text, reply_markup=lead_keyboard)
    return JsonResponse({"ok": True})


@csrf_exempt
def telegram_webhook_view(request):
    """Telegram bot webhook — handles commands and callbacks."""
    if request.method != "POST":
        return HttpResponse("ok")
    try:
        update = json.loads(request.body)
    except Exception:
        return HttpResponse("bad request", status=400)

    msg = update.get("message") or {}
    cb = update.get("callback_query") or {}

    # ── Callback query (inline button press) ──
    if cb:
        chat_id = str(cb.get("chat", {}).get("id", ""))
        cb_id = cb.get("id")
        data = cb.get("data", "")
        _tg_answer_callback(cb_id)

        if str(chat_id) not in _get_admin_ids():
            _tg_send(chat_id, "⛔ Нет доступа.")
            return HttpResponse("ok")

        if data == "stats":
            from apps.landing.models import ContactSubmission as CS
            total = CS.objects.count()
            today = CS.objects.filter(created_at__date=datetime.now().date()).count()
            _tg_send(chat_id,
                f"<b>📊 Статистика заявок</b>\n\n"
                f"Всего заявок: <b>{total}</b>\n"
                f"Сегодня: <b>{today}</b>",
                reply_markup=_MAIN_KEYBOARD)

        elif data == "leads_recent":
            from apps.landing.models import ContactSubmission as CS
            leads = CS.objects.order_by("-created_at")[:5]
            if not leads:
                _tg_send(chat_id, "Заявок пока нет.", reply_markup=_MAIN_KEYBOARD)
            else:
                lines = ["<b>📋 Последние 5 заявок:</b>\n"]
                for l in leads:
                    lines.append(
                        f"#{l.pk} · {l.created_at:%d.%m %H:%M}\n"
                        f"👤 {l.name} | 📞 {l.phone or '—'} | 📧 {l.email or '—'}\n"
                    )
                _tg_send(chat_id, "\n".join(lines), reply_markup=_MAIN_KEYBOARD)

        elif data.startswith("lead_done_"):
            lead_id = data.split("_")[-1]
            _tg_send(chat_id, f"✅ Заявка #{lead_id} отмечена как обработанная.")

        return HttpResponse("ok")

    # ── Text commands ──
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = (msg.get("text") or "").strip()

    if not chat_id or not text:
        return HttpResponse("ok")

    if str(chat_id) not in _get_admin_ids():
        _tg_send(chat_id, "👋 Привет! Этот бот только для администраторов TCC.")
        return HttpResponse("ok")

    if text.startswith("/start"):
        from apps.landing.models import ContactSubmission as CS
        total = CS.objects.count()
        today = CS.objects.filter(created_at__date=datetime.now().date()).count()
        _tg_send(chat_id,
            "👋 <b>TCC HUB — Административный бот</b>\n\n"
            "Добро пожаловать! Этот бот помогает управлять сайтом "
            "<b>TransCaspian Cargo</b> и получать уведомления о заявках.\n\n"
            "<b>Что умеет бот:</b>\n"
            "📩 Уведомления о новых заявках с сайта\n"
            "📋 Просмотр последних заявок\n"
            "📊 Статистика заявок\n"
            "🔗 Быстрые ссылки на сайт и админ-панель\n\n"
            f"<b>Статистика сегодня:</b> {today} заявок · Всего: {total}\n\n"
            "Выберите действие 👇",
            reply_markup=_MAIN_KEYBOARD)

    elif text.startswith("/zaявки") or text.startswith("/leads"):
        from apps.landing.models import ContactSubmission as CS
        leads = CS.objects.order_by("-created_at")[:5]
        if not leads:
            _tg_send(chat_id, "Заявок пока нет.")
        else:
            lines = ["<b>📋 Последние заявки:</b>\n"]
            for l in leads:
                lines.append(f"#{l.pk} · {l.name} | {l.phone or '—'} | {l.created_at:%d.%m %H:%M}")
            _tg_send(chat_id, "\n".join(lines), reply_markup=_MAIN_KEYBOARD)

    elif text.startswith("/stats"):
        from apps.landing.models import ContactSubmission as CS
        total = CS.objects.count()
        today = CS.objects.filter(created_at__date=datetime.now().date()).count()
        _tg_send(chat_id, f"📊 Всего заявок: <b>{total}</b>\nСегодня: <b>{today}</b>", reply_markup=_MAIN_KEYBOARD)

    else:
        _tg_send(chat_id,
            "Команды:\n/start — меню\n/leads — последние заявки\n/stats — статистика",
            reply_markup=_MAIN_KEYBOARD)

    return HttpResponse("ok")


def wiki_view(request):
    return render(request, "site/wiki.html", {"active_page": "wiki"})


def kz_logistics_laws_view(request):
    return render(request, "site/kz_logistics_laws.html", {"active_page": "kz_logistics_laws"})


# ──────────────────────────────────────────────
# Tools (login required)
# ──────────────────────────────────────────────

@login_required
def corridor_view(request):
    return render(request, "site/corridor.html", {"active_page": "corridor"})


@login_required
def corridor_map_view(request):
    return render(request, "site/corridor_map.html", {"active_page": "corridor_map"})


@login_required
def live_data_view(request):
    return render(request, "site/live_data.html", {"active_page": "live_data"})


@login_required
def monitoring_view(request):
    return render(request, "site/monitoring.html", {"active_page": "monitoring"})


@login_required
def export_route_scores_view(request):
    from apps.tcc_data.exports import export_route_scores_csv
    return export_route_scores_csv(request)


@login_required
def export_risk_factors_view(request):
    from apps.tcc_data.exports import export_risk_factors_csv
    return export_risk_factors_csv(request)


@login_required
def export_trade_flows_view(request):
    from apps.tcc_data.exports import export_trade_flows_csv
    return export_trade_flows_csv(request)


@login_required
def export_sanctions_view(request):
    from apps.tcc_data.exports import export_sanctions_csv
    return export_sanctions_csv(request)


# ──────────────────────────────────────────────
# Articles
# ──────────────────────────────────────────────

ARTICLES = {
    "transkaspiyskiy-marshrut": {
        "title": "Транскаспийский маршрут: пятикратный рост за 7 лет",
        "slug": "transkaspiyskiy-marshrut",
        "tag": "Отраслевой обзор · Средний коридор",
        "date": "12 декабря 2024",
        "read_time": "8 мин",
        "image_url": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Грузопоток", "value": "4.5 млн тонн"},
            {"label": "Инвестиционный разрыв", "value": "EUR 18.5 млрд"},
            {"label": "Рост за 7 лет", "value": "5x"},
            {"label": "Срок доставки", "value": "12-15 дней"},
        ],
        "content": [
            {"type": "text", "body": "Транскаспийский международный транспортный маршрут (ТМТМ), также известный как Средний коридор, стал одним из ключевых элементов новой евразийской логистической архитектуры. За период с 2017 по 2024 год грузопоток по маршруту увеличился с 0.9 млн тонн до 4.5 млн тонн, продемонстрировав пятикратный рост, который обусловлен как геополитическими сдвигами, так и масштабными инвестициями в инфраструктуру."},
            {"type": "heading", "level": 2, "body": "Динамика роста грузоперевозок"},
            {"type": "text", "body": "Стартовав с относительно скромных показателей в 0.9 млн тонн в 2017 году, маршрут демонстрировал устойчивый рост, обусловленный несколькими факторами. Первоначальный импульс дало подписание многосторонних соглашений между Казахстаном, Азербайджаном, Грузией и Турцией о упрощении транзитных процедур. Ежегодный прирост составлял от 20 до 30 процентов, при этом наиболее значительное ускорение наблюдалось в 2022-2024 годах, когда санкционное давление и кризис в Красном море перенаправили часть грузопотоков с традиционных морских маршрутов."},
            {"type": "chart_bar", "title": "Грузопоток по ТМТМ, 2017-2024 (млн тонн)", "bars": [
                {"label": "2017", "value": 0.9, "max": 4.5, "display": "0.9 млн т"},
                {"label": "2018", "value": 1.2, "max": 4.5, "display": "1.2 млн т"},
                {"label": "2019", "value": 1.5, "max": 4.5, "display": "1.5 млн т"},
                {"label": "2020", "value": 2.0, "max": 4.5, "display": "2.0 млн т"},
                {"label": "2021", "value": 2.5, "max": 4.5, "display": "2.5 млн т"},
                {"label": "2022", "value": 3.1, "max": 4.5, "display": "3.1 млн т"},
                {"label": "2023", "value": 3.8, "max": 4.5, "display": "3.8 млн т"},
                {"label": "2024", "value": 4.5, "max": 4.5, "display": "4.5 млн т"},
            ]},
            {"type": "heading", "level": 2, "body": "Инвестиционный разрыв: EUR 18.5 млрд"},
            {"type": "text", "body": "Несмотря на впечатляющую динамику, Средний коридор сталкивается с серьёзным вызовом — инвестиционным разрывом, оцениваемым в EUR 18.5 млрд. Основные потребности сосредоточены в портовой инфраструктуре Каспийского моря, модернизации железнодорожных путей в Грузии и Азербайджане, а также в строительстве современных мультимодальных терминалов. Европейский банк реконструкции и развития (ЕБРР) и Азиатский банк инфраструктурных инвестиций (АБИИ) уже выделили первые транши, однако для достижения целевых показателей необходимо привлечение частного капитала."},
            {"type": "stats_grid", "items": [
                {"label": "Грузопоток 2024", "value": "4.5 млн тонн"},
                {"label": "Инвестразрыв", "value": "EUR 18.5 млрд"},
                {"label": "Рост с 2017", "value": "5x"},
                {"label": "Доставка", "value": "12-15 дней"},
            ]},
            {"type": "heading", "level": 2, "body": "Модернизация порта Актау"},
            {"type": "text", "body": "Порт Актау является ключевым звеном Среднего коридора на казахстанском участке. В 2023-2024 годах Казахстан инвестировал $3 млрд в масштабную модернизацию порта, включающую расширение контейнерного терминала, углубление акватории для приёма крупнотоннажных судов и строительство нового железнодорожного паромного причала. Пропускная способность порта увеличена до 100 000 TEU в год, что вдвое превышает показатели 2020 года. Параллельно ведётся строительство логистического хаба «Актау Сити» с зоной свободной торговли и таможенным терминалом."},
            {"type": "quote", "body": "Средний коридор — это не просто транспортный маршрут, а стратегический мост между Азией и Европой, значение которого будет только расти в условиях новой геополитической реальности.", "author": "Аналитический отдел TCC Hub"},
            {"type": "heading", "level": 2, "body": "Сравнение с альтернативными коридорами"},
            {"type": "text", "body": "По сравнению с традиционным морским маршрутом через Суэцкий канал, Средний коридор предлагает доставку за 12-15 дней вместо 30-45 дней. Относительно Северного морского пути, ТМТМ выигрывает по стабильности (круглогодичная навигация) и предсказуемости расписания. В сравнении с железнодорожным маршрутом через Россию, Средний коридор обеспечивает снижение санкционных рисков и диверсификацию логистических цепочек."},
            {"type": "list", "items": [
                "Морской путь через Суэц: 30-45 дней, но подвержен кризисам в Красном море",
                "Северный морской путь: ограничен 4-5 месяцами навигации в году",
                "Ж/д через Россию: 14-16 дней, но подвержен санкционным рискам",
                "Средний коридор (ТМТМ): 12-15 дней, круглогодичная стабильная работа",
            ]},
            {"type": "heading", "level": 2, "body": "Цели до 2030 года"},
            {"type": "text", "body": "Страны-участницы ТМТМ поставили амбициозную цель — довести грузопоток до 10 млн тонн к 2030 году. Для этого необходимо не только закрыть инвестиционный разрыв, но и гармонизировать таможенные процедуры, внедрить единую цифровую систему отслеживания грузов и оптимизировать тарифную политику. По оценкам экспертов, при условии реализации запланированных инвестиций и сохранении текущих геополитических трендов, цель в 10 млн тонн вполне достижима. Ключевым фактором станет развитие контейнерных перевозок, доля которых сейчас составляет менее 15% от общего грузопотока."},
        ],
    },
    "sanktsii-peremarshrutizatsiya": {
        "title": "Санкции и перемаршрутизация: новая логистическая карта Евразии",
        "slug": "sanktsii-peremarshrutizatsiya",
        "tag": "Аналитическая статья · Санкционные риски",
        "date": "28 ноября 2024",
        "read_time": "10 мин",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Суэцкий канал", "value": "-90% трафика"},
            {"label": "Фрахтовые ставки", "value": "+80%"},
            {"label": "Сухопутные коридоры", "value": "+14%"},
            {"label": "Новая архитектура", "value": "к 2027"},
        ],
        "content": [
            {"type": "text", "body": "Кризис в Красном море, западные санкции и растущая геополитическая нестабильность кардинально меняют глобальную логистическую карту. Впервые за последние десятилетия сухопутные коридоры Евразии получают стратегическое преимущество перед морскими маршрутами, формируя принципиально новую архитектуру товарных потоков между Азией и Европой."},
            {"type": "heading", "level": 2, "body": "Кризис Суэцкого канала и его последствия"},
            {"type": "text", "body": "Атаки хуситов на торговые суда в Красном море привели к падению трафика через Суэцкий канал на 90%. Крупнейшие контейнерные линии — Maersk, MSC, CMA CGM — перенаправили флот вокруг мыса Доброй Надежды, что увеличило время доставки на 7-10 дней и стоимость фрахта в 2.5 раза. Суммарный экономический ущерб от перенаправления оценивается в $120-150 млрд в год для мировой торговли. Страховые премии для судов, проходящих через Красное море, выросли в 10 раз, сделав этот маршрут экономически нецелесообразным для большинства перевозчиков."},
            {"type": "chart_bar", "title": "Сравнение роста грузопотоков: морские vs сухопутные, 2024", "bars": [
                {"label": "Суэцкий канал", "value": 10, "max": 100, "display": "-90%"},
                {"label": "Мыс Д. Надежды", "value": 85, "max": 100, "display": "+350%"},
                {"label": "ТМТМ", "value": 65, "max": 100, "display": "+40%"},
                {"label": "Ж/д Китай-Европа", "value": 58, "max": 100, "display": "+14%"},
                {"label": "Сев. морской путь", "value": 45, "max": 100, "display": "+8%"},
            ]},
            {"type": "heading", "level": 2, "body": "Резкий рост фрахтовых ставок"},
            {"type": "text", "body": "Средние ставки фрахта на направлении Азия–Европа выросли на 80% за 2024 год, достигнув уровня пандемийных максимумов. Стоимость перевозки 40-футового контейнера из Шанхая в Роттердам превысила $7,500 в пиковые месяцы. Увеличение сроков доставки привело к дефициту контейнеров в азиатских портах и перегрузке европейских терминалов. Грузовладельцы были вынуждены закладывать дополнительные 15-20% к бюджету логистики, что повлияло на конечные цены товаров в Европе."},
            {"type": "stats_grid", "items": [
                {"label": "Падение Суэца", "value": "-90%"},
                {"label": "Рост ставок", "value": "+80%"},
                {"label": "Сухопутные +", "value": "+14%"},
                {"label": "Страховка x", "value": "10 раз"},
            ]},
            {"type": "heading", "level": 2, "body": "Перемаршрутизация на сухопутные коридоры"},
            {"type": "text", "body": "Сухопутные коридоры через Центральную Азию получили дополнительный грузопоток на 14% по сравнению с аналогичным периодом предыдущего года. Средний коридор (ТМТМ) зафиксировал рост заявок на перевозку на 40%, при этом время обработки грузов на ключевых узлах сократилось благодаря цифровизации таможенных процедур. Железнодорожные контейнерные перевозки Китай-Европа по всем маршрутам суммарно выросли на 14%, причём наибольший рост показал именно Средний коридор."},
            {"type": "quote", "body": "Мы наблюдаем формирование параллельной логистической архитектуры Евразии, где сухопутные коридоры перестают быть дополнением к морским маршрутам и становятся полноценной альтернативой.", "author": "Аналитический центр TCC Hub"},
            {"type": "heading", "level": 2, "body": "Формирование новой логистической архитектуры"},
            {"type": "text", "body": "Эксперты прогнозируют, что к 2027 году сформируется принципиально новая логистическая архитектура Евразии, основанная на диверсификации маршрутов. Ключевые элементы этой архитектуры — Средний коридор, коридор Север-Юг (INSTC), модернизированные железнодорожные маршруты через Казахстан и Северный морской путь. Страны Центральной Азии, в первую очередь Казахстан, становятся критически важным транзитным звеном, инвестируя в инфраструктуру и цифровизацию логистических процессов."},
            {"type": "list", "items": [
                "Средний коридор получает до 40% дополнительных заявок на грузоперевозки",
                "Страховые премии в Красном море выросли в 10 раз, делая морской маршрут нерентабельным",
                "Новые мультимодальные хабы строятся в Актау, Баку и Поти",
                "Цифровая таможня сокращает время обработки грузов на 40%",
                "К 2027 году ожидается формирование устойчивой параллельной логистической системы",
            ]},
        ],
    },
    "konteynernyy-rynok-evrazii": {
        "title": "Контейнерный рынок Евразии 2025-2026",
        "slug": "konteynernyy-rynok-evrazii",
        "tag": "Исследование рынка · Логистика Евразии",
        "date": "15 ноября 2024",
        "read_time": "9 мин",
        "image_url": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Китай-Европа (море)", "value": "-18%"},
            {"label": "Средний коридор", "value": "+14%"},
            {"label": "Хоргос", "value": "372K TEU"},
            {"label": "Актау терминал", "value": "100K TEU/год"},
        ],
        "content": [
            {"type": "text", "body": "Контейнерный рынок Евразии переживает период структурной трансформации. Традиционные морские маршруты теряют объёмы, в то время как сухопутные коридоры и железнодорожные перевозки показывают устойчивый рост. Обзор охватывает ключевые тенденции 2024 года и прогнозы на 2025-2026 годы, с фокусом на Центральноазиатский регион и его роль в глобальных контейнерных потоках."},
            {"type": "heading", "level": 2, "body": "Снижение морских контейнерных перевозок"},
            {"type": "text", "body": "Объём контейнерных перевозок по маршруту Китай–Европа через морские порты снизился на 18% по сравнению с 2023 годом. Основные причины — кризис в Красном море, рост фрахтовых ставок и увеличение сроков доставки. Перенаправление судов вокруг мыса Доброй Надежды добавляет 7-10 дней к стандартному транзитному времени и увеличивает расход топлива на 30%. Крупные грузовладельцы, такие как автомобильные концерны и производители электроники, активно диверсифицируют логистические цепочки, переключая часть объёмов на железнодорожные маршруты."},
            {"type": "chart_bar", "title": "Контейнерные объёмы по коридорам, 2024 (тыс. TEU)", "bars": [
                {"label": "Морской (Суэц)", "value": 45, "max": 100, "display": "12,400 TEU"},
                {"label": "Морской (Доброй Над.)", "value": 72, "max": 100, "display": "19,800 TEU"},
                {"label": "Ж/д через РФ", "value": 68, "max": 100, "display": "680K TEU"},
                {"label": "ТМТМ", "value": 38, "max": 100, "display": "372K TEU"},
                {"label": "Сев. морской путь", "value": 12, "max": 100, "display": "48K TEU"},
            ]},
            {"type": "heading", "level": 2, "body": "Рекорд сухого порта Хоргос"},
            {"type": "text", "body": "Международный центр приграничного сотрудничества «Хоргос» на границе Китая и Казахстана обработал рекордные 372 000 TEU в 2024 году, превысив показатели предыдущего года на 28%. Расширение мощностей включает запуск третьей очереди контейнерного терминала, внедрение автоматизированной системы перестановки колёсных пар (с китайской на широкую колею) и создание зоны электронной коммерции. Время обработки одного контейнера сократилось до 4 часов благодаря цифровому таможенному оформлению."},
            {"type": "stats_grid", "items": [
                {"label": "Море Китай-Европа", "value": "-18%"},
                {"label": "Средний коридор", "value": "+14%"},
                {"label": "Хоргос рекорд", "value": "372K TEU"},
                {"label": "Актау мощность", "value": "100K TEU"},
            ]},
            {"type": "heading", "level": 2, "body": "Новый контейнерный терминал в Актау"},
            {"type": "text", "body": "Порт Актау запустил новый контейнерный терминал мощностью 100 000 TEU в год, ставший ключевым элементом мультимодальной логистической цепочки Среднего коридора. Терминал оснащён современными портальными кранами, системой автоматического складирования и прямым железнодорожным подъездом. Груз, прибывающий железной дорогой из Хоргоса, перегружается на суда Каспийского моря для дальнейшей транспортировки в Баку, откуда продолжает путь по железной дороге через Грузию в порты Черного моря."},
            {"type": "heading", "level": 2, "body": "Железнодорожные контейнерные перевозки"},
            {"type": "text", "body": "Железнодорожные контейнерные перевозки через Казахстан продемонстрировали рост на 14% в 2024 году. Ключевой драйвер — увеличение регулярности контейнерных поездов на маршрутах Сиань-Алматы-Стамбул и Чунцин-Хоргос-Баку-Поти. Средняя скорость транзита составляет 900-1100 км в сутки, что обеспечивает доставку из Китая в Турцию за 12-14 дней. Операторы контейнерных поездов KTZ Express и ADY Container отмечают устойчивый рост спроса и планируют увеличение частоты отправок."},
            {"type": "quote", "body": "Контейнеризация грузов — главный драйвер роста Среднего коридора. Если в 2020 году доля контейнеров составляла 8%, то к 2025 году она достигнет 18-20%.", "author": "Исследовательский отдел TCC Hub"},
            {"type": "heading", "level": 2, "body": "Прогноз на 2025-2026"},
            {"type": "text", "body": "При сохранении кризиса в Красном море прогнозируется дальнейший рост сухопутных контейнерных перевозок на 10-15% ежегодно. Хоргос планирует достичь 500 000 TEU к 2026 году за счёт запуска четвёртой очереди терминала. Порт Актау нарастит мощности до 150 000 TEU при условии завершения второй фазы расширения. Ключевым вызовом остаётся дефицит порожних контейнеров на обратном направлении Европа-Китай, который увеличивает стоимость перевозки и снижает эффективность использования вагонного парка."},
            {"type": "list", "items": [
                "Хоргос: цель 500K TEU к 2026 году (+34% к текущим показателям)",
                "Актау: расширение до 150K TEU, вторая фаза строительства",
                "Запуск контейнерного поезда Ляньюньган-Стамбул через ТМТМ (еженедельно)",
                "Цифровой коносамент (e-BL) планируется внедрить на всём маршруте к 2025",
                "Дефицит порожних контейнеров остаётся основным вызовом для операторов",
            ]},
        ],
    },
    "koridor-sever-yug": {
        "title": "Коридор Север-Юг: 26.9 млн тонн",
        "slug": "koridor-sever-yug",
        "tag": "Экспертный отчёт · Средний коридор",
        "date": "3 ноября 2024",
        "read_time": "9 мин",
        "image_url": "https://images.unsplash.com/photo-1605732562742-3023a888e56e?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Рост INSTC", "value": "+19%"},
            {"label": "Грузопоток", "value": "26.9 млн тонн"},
            {"label": "Новый участник", "value": "Пакистан"},
            {"label": "Доставка", "value": "14-18 дней"},
        ],
        "content": [
            {"type": "text", "body": "Международный транспортный коридор Север-Юг (INSTC) продолжает набирать обороты, достигнув рекордного грузопотока в 26.9 млн тонн за 2024 год. Коридор, соединяющий Россию, Иран и Индию с выходом на порты Персидского залива и Индийского океана, становится стратегической альтернативой Суэцкому каналу для торговли между Евразией и Южной Азией."},
            {"type": "heading", "level": 2, "body": "Рекордный грузопоток"},
            {"type": "text", "body": "Общий грузопоток по INSTC достиг 26.9 млн тонн, показав рост на 19% к предыдущему году. Основной объём приходится на навалочные грузы — зерно, минеральные удобрения, металлы и нефтепродукты. Контейнерный сегмент, хотя и составляет пока менее 5% от общего объёма, демонстрирует наиболее динамичный рост — на 34% за год. Ключевые грузопотоки формируются на направлениях Россия–Иран, Россия–Индия и Казахстан–Иран–Индия."},
            {"type": "chart_bar", "title": "Грузопоток INSTC по годам (млн тонн)", "bars": [
                {"label": "2019", "value": 14.5, "max": 26.9, "display": "14.5 млн т"},
                {"label": "2020", "value": 16.2, "max": 26.9, "display": "16.2 млн т"},
                {"label": "2021", "value": 18.1, "max": 26.9, "display": "18.1 млн т"},
                {"label": "2022", "value": 20.5, "max": 26.9, "display": "20.5 млн т"},
                {"label": "2023", "value": 22.6, "max": 26.9, "display": "22.6 млн т"},
                {"label": "2024", "value": 26.9, "max": 26.9, "display": "26.9 млн т"},
            ]},
            {"type": "heading", "level": 2, "body": "Присоединение Пакистана"},
            {"type": "text", "body": "Знаковым событием 2024 года стало официальное присоединение Пакистана к проекту INSTC. Это открывает доступ к портам Гвадар и Карачи, существенно расширяя географию маршрута. Пакистанский участок предполагает использование автомобильных и железнодорожных маршрутов через Белуджистан для подключения к иранской транспортной сети. Ожидается, что присоединение Пакистана добавит к грузопотоку INSTC дополнительные 3-5 млн тонн ежегодно к 2027 году, преимущественно за счёт текстиля, сельскохозяйственной продукции и минерального сырья."},
            {"type": "stats_grid", "items": [
                {"label": "Грузопоток 2024", "value": "26.9 млн т"},
                {"label": "Рост", "value": "+19%"},
                {"label": "Контейнеры", "value": "+34%"},
                {"label": "Транзит", "value": "14-18 дн."},
            ]},
            {"type": "heading", "level": 2, "body": "Железнодорожный участок Решт–Астара"},
            {"type": "text", "body": "Иран активно завершает строительство железнодорожного участка Решт–Астара протяжённостью 164 км — критического звена западной ветки коридора. Этот участок соединит иранскую железнодорожную сеть с азербайджанской, обеспечив непрерывное железнодорожное сообщение от порта Бендер-Аббас на юге Ирана до Баку и далее до России. Завершение строительства запланировано на 2025 год, после чего ожидается существенное сокращение транзитного времени и стоимости перевозки. Россия выделила $1.6 млрд кредита на реализацию проекта."},
            {"type": "heading", "level": 2, "body": "Время доставки: Мумбаи–Москва"},
            {"type": "text", "body": "Одно из главных конкурентных преимуществ INSTC — радикальное сокращение времени доставки. Маршрут Мумбаи–Москва по коридору Север-Юг занимает 14-18 дней, тогда как традиционный морской путь через Суэцкий канал — 45-60 дней. Стоимость перевозки также ниже: $2,500-3,500 за контейнер по INSTC против $5,000-7,000 через Суэц (с учётом возросших страховых премий). Ключевой мультимодальный узел — порт Бендер-Аббас, откуда грузы следуют по железной дороге через Иран до Астары, далее морем до Астрахани и по внутренним водным путям России."},
            {"type": "quote", "body": "INSTC — это ответ на вопрос о том, как соединить Индийский океан с Северной Евразией без зависимости от Суэца. С присоединением Пакистана маршрут обретает критическую массу.", "author": "Экспертный совет TCC Hub"},
            {"type": "heading", "level": 2, "body": "Расширение порта Астрахань"},
            {"type": "text", "body": "Россия инвестирует в масштабное расширение порта Астрахань, который является северным терминалом Каспийского моря на коридоре Север-Юг. Проект предусматривает строительство нового грузового терминала мощностью 8 млн тонн, углубление фарватера для судов дедвейтом до 10 000 тонн и модернизацию Каспийского флота с постройкой 15 новых грузовых судов класса «река-море». Общий объём инвестиций составляет $2.3 млрд. Завершение первой очереди ожидается в 2026 году."},
        ],
    },
    "tsifrovaya-transformatsiya": {
        "title": "Цифровая трансформация логистики Центральной Азии",
        "slug": "tsifrovaya-transformatsiya",
        "tag": "Аналитическая статья · Трансформация цепей поставок",
        "date": "18 октября 2024",
        "read_time": "8 мин",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Время оформления", "value": "-40%"},
            {"label": "ASYCUDAWorld", "value": "5 стран"},
            {"label": "E-commerce", "value": "+35%"},
            {"label": "ИИ-экономия", "value": "-12% издержки"},
        ],
        "content": [
            {"type": "text", "body": "Центральная Азия переживает масштабную цифровую трансформацию логистической инфраструктуры. Внедрение современных информационных систем, автоматизация таможенных процедур, рост электронной коммерции и применение искусственного интеллекта в оптимизации маршрутов создают новое качество транспортно-логистических услуг в регионе. Эти изменения критически важны для реализации потенциала транзитных коридоров."},
            {"type": "heading", "level": 2, "body": "Внедрение ASYCUDAWorld"},
            {"type": "text", "body": "Автоматизированная система таможенного администрирования ASYCUDAWorld, разработанная ЮНКТАД, внедрена во всех пяти странах Центральной Азии — Казахстане, Узбекистане, Кыргызстане, Таджикистане и Туркменистане. Система обеспечивает единую базу данных таможенных операций, электронное декларирование и управление рисками. Казахстан, как лидер внедрения, интегрировал ASYCUDAWorld с национальной системой «Астана-1», что позволило сократить время таможенного оформления на 40% и перевести 96% деклараций в электронный формат."},
            {"type": "chart_bar", "title": "Цифровизация таможни: сравнение стран региона", "bars": [
                {"label": "Казахстан", "value": 92, "max": 100, "display": "92% электронных деклараций"},
                {"label": "Узбекистан", "value": 78, "max": 100, "display": "78% электронных деклараций"},
                {"label": "Кыргызстан", "value": 65, "max": 100, "display": "65% электронных деклараций"},
                {"label": "Таджикистан", "value": 52, "max": 100, "display": "52% электронных деклараций"},
                {"label": "Туркменистан", "value": 38, "max": 100, "display": "38% электронных деклараций"},
            ]},
            {"type": "heading", "level": 2, "body": "Цифровая таможня и электронное декларирование"},
            {"type": "text", "body": "Переход к цифровой таможне — один из ключевых факторов повышения конкурентоспособности транзитных коридоров Центральной Азии. Электронное декларирование, предварительное информирование и система управления рисками позволяют значительно сократить время на границе. В Казахстане среднее время таможенного оформления экспортной партии сократилось с 72 до 43 часов, а импортной — с 96 до 58 часов. Узбекистан внедрил систему «Единое окно» для внешнеторговых операций, объединив 16 государственных ведомств на одной платформе."},
            {"type": "stats_grid", "items": [
                {"label": "Сокращение времени", "value": "-40%"},
                {"label": "ASYCUDAWorld", "value": "5 стран"},
                {"label": "E-commerce рост", "value": "+35%"},
                {"label": "ИИ-экономия", "value": "-12%"},
            ]},
            {"type": "heading", "level": 2, "body": "Рост электронной коммерции"},
            {"type": "text", "body": "Объём электронной коммерции в Центральной Азии вырос на 35% за 2024 год, создавая принципиально новый спрос на логистику последней мили. Казахстан лидирует с объёмом рынка $4.2 млрд, за ним следуют Узбекистан ($1.8 млрд) и Кыргызстан ($0.4 млрд). Рост e-commerce стимулирует создание распределительных центров, развитие курьерских сервисов и внедрение автоматизированных сортировочных линий. Маркетплейсы Kaspi, Uzum и Wildberries активно инвестируют в логистическую инфраструктуру региона."},
            {"type": "heading", "level": 2, "body": "Блокчейн-отслеживание грузов"},
            {"type": "text", "body": "Блокчейн-платформы для отслеживания грузов проходят пилотное тестирование на маршруте Алматы–Ташкент–Стамбул. Технология обеспечивает прозрачность всей цепочки поставок, неизменяемость данных о происхождении и движении груза, а также автоматическое исполнение смарт-контрактов при прохождении контрольных точек. Пилотный проект охватывает 120 отправок ежемесячно и показывает сокращение времени на документальное оформление на 60%. При успешном завершении пилота планируется масштабирование на весь Средний коридор к 2026 году."},
            {"type": "quote", "body": "Цифровизация — единственный способ сделать сухопутные коридоры по-настоящему конкурентоспособными с морскими маршрутами по критерию стоимости и предсказуемости.", "author": "Цифровой отдел TCC Hub"},
            {"type": "heading", "level": 2, "body": "ИИ-оптимизация маршрутов"},
            {"type": "text", "body": "Искусственный интеллект всё активнее применяется для оптимизации транспортных маршрутов в регионе. Крупные логистические операторы используют алгоритмы машинного обучения для прогнозирования загрузки терминалов, оптимизации расписания поездов и выбора оптимального маршрута с учётом текущих условий. Результаты впечатляют: ИИ-оптимизация снижает транспортные издержки на 8-12% для крупных операторов и сокращает время простоя на 25%. KTZ Express запустил ИИ-платформу для динамического ценообразования и управления вагонным парком, охватывающую 15 000 вагонов."},
            {"type": "list", "items": [
                "ASYCUDAWorld внедрён во всех 5 странах Центральной Азии",
                "96% таможенных деклараций в Казахстане — электронные",
                "Блокчейн-пилот на маршруте Алматы–Ташкент–Стамбул: -60% время документации",
                "ИИ-оптимизация маршрутов: экономия 8-12% логистических издержек",
                "E-commerce в ЦА: $6.4 млрд общий объём, рост 35% за год",
            ]},
        ],
    },
    "kazakhstan-tranzitnyy-hab": {
        "title": "Казахстан: 36.9 млн тонн транзита и амбиции хаба",
        "slug": "kazakhstan-tranzitnyy-hab",
        "tag": "Исследование рынка · Логистика Евразии",
        "date": "5 октября 2024",
        "read_time": "9 мин",
        "image_url": "https://images.unsplash.com/photo-1545128485-c400e7702796?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Транзит", "value": "36.9 млн тонн"},
            {"label": "Хоргос", "value": "372K TEU"},
            {"label": "Программа", "value": "$9 млрд Nurly Zhol"},
            {"label": "Цель", "value": "Хаб №1 к 2030"},
        ],
        "content": [
            {"type": "text", "body": "Казахстан уверенно движется к реализации стратегической цели — стать ключевым транзитным хабом между Азией и Европой. Общий объём транзитных грузов через территорию страны достиг рекордных 36.9 млн тонн в 2024 году, подтверждая географическое и инфраструктурное преимущество Казахстана на пересечении основных евразийских транспортных коридоров."},
            {"type": "heading", "level": 2, "body": "Рекордные транзитные объёмы"},
            {"type": "text", "body": "Транзитный грузопоток через Казахстан достиг 36.9 млн тонн — абсолютный рекорд за всю историю независимости. Железнодорожный транзит составил 27.4 млн тонн (+16%), автомобильный — 6.2 млн тонн (+11%), морской (через порты Каспия) — 3.3 млн тонн (+22%). Основные грузопотоки формируются на направлениях Китай–Европа, Китай–Центральная Азия, Россия–Центральная Азия и INSTC. Доля контейнерных грузов в транзите выросла до 12%, продолжая устойчивый тренд контейнеризации."},
            {"type": "chart_bar", "title": "Транзит через Казахстан по годам (млн тонн)", "bars": [
                {"label": "2019", "value": 19.8, "max": 36.9, "display": "19.8 млн т"},
                {"label": "2020", "value": 21.5, "max": 36.9, "display": "21.5 млн т"},
                {"label": "2021", "value": 25.2, "max": 36.9, "display": "25.2 млн т"},
                {"label": "2022", "value": 28.7, "max": 36.9, "display": "28.7 млн т"},
                {"label": "2023", "value": 32.1, "max": 36.9, "display": "32.1 млн т"},
                {"label": "2024", "value": 36.9, "max": 36.9, "display": "36.9 млн т"},
            ]},
            {"type": "heading", "level": 2, "body": "Сухой порт Хоргос: ворота Китая"},
            {"type": "text", "body": "Международный центр приграничного сотрудничества «Хоргос» стал визитной карточкой транзитного потенциала Казахстана. В 2024 году через Хоргос прошло 372 000 TEU — рост на 28% к предыдущему году. Сухой порт оснащён четырьмя контейнерными терминалами, автоматизированной системой перестановки колёсных пар и зоной свободной торговли. Казахстанская и китайская стороны совместно инвестируют в расширение инфраструктуры — цель на 2026 год составляет 500 000 TEU."},
            {"type": "stats_grid", "items": [
                {"label": "Транзит 2024", "value": "36.9 млн т"},
                {"label": "Хоргос", "value": "372K TEU"},
                {"label": "Nurly Zhol", "value": "$9 млрд"},
                {"label": "Ж/д транзит", "value": "+16%"},
            ]},
            {"type": "heading", "level": 2, "body": "Программа «Нурлы Жол»"},
            {"type": "text", "body": "Государственная программа инфраструктурного развития «Нурлы Жол» (Светлый путь) предусматривает $9 млрд инвестиций в транспортную инфраструктуру до 2029 года. Ключевые направления: модернизация 4 500 км железнодорожных путей, строительство 2 200 км новых автодорог, расширение портов Актау и Курык, создание 5 мультимодальных логистических центров. Программа финансируется из государственного бюджета, средств Национального фонда и международных финансовых институтов (ЕБРР, АБР, АБИИ)."},
            {"type": "heading", "level": 2, "body": "Мультимодальный хаб Актау"},
            {"type": "text", "body": "Порт Актау трансформируется из традиционного нефтяного терминала в современный мультимодальный хаб. Новый контейнерный терминал (100K TEU/год), паромная переправа для железнодорожных вагонов (6 причалов), зона свободной торговли и логистический парк создают полноценный транзитный узел для Среднего коридора. Параллельно развивается порт Курык — второй каспийский порт Казахстана, специализирующийся на перевалке сухих грузов и нефтепродуктов. Суммарная пропускная способность каспийских портов Казахстана достигнет 30 млн тонн к 2027 году."},
            {"type": "quote", "body": "Казахстан — естественный мост между Азией и Европой. Наша задача — превратить географическое преимущество в экономическое за счёт инфраструктуры мирового уровня.", "author": "По материалам стратегии «Нурлы Жол»"},
            {"type": "heading", "level": 2, "body": "Цель: хаб №1 Китай–Европа к 2030"},
            {"type": "text", "body": "Казахстан поставил амбициозную цель стать главным транзитным хабом для грузов на направлении Китай–Европа к 2030 году. Для этого реализуется комплексная стратегия, включающая инфраструктурные инвестиции (Нурлы Жол), упрощение таможенных процедур (Единое окно), цифровизацию логистики (ИИ, блокчейн) и тарифную политику (субсидии на транзитные перевозки). По оценкам Министерства транспорта РК, к 2030 году транзитный грузопоток может достичь 50 млн тонн при условии реализации всех запланированных проектов."},
            {"type": "list", "items": [
                "Транзит через Казахстан: 36.9 млн тонн (рекорд 2024)",
                "Хоргос: 372K TEU, цель — 500K TEU к 2026",
                "Нурлы Жол: $9 млрд инвестиций до 2029",
                "Каспийские порты: мощность 30 млн тонн к 2027",
                "Цель к 2030: 50 млн тонн транзита, хаб №1 Китай–Европа",
            ]},
        ],
    },
    "bri-2025": {
        "title": "BRI 2025: рекордные $128 млрд контрактов",
        "slug": "bri-2025",
        "tag": "Отраслевой обзор · Логистика Евразии",
        "date": "22 сентября 2024",
        "read_time": "8 мин",
        "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "BRI контракты", "value": "$128 млрд"},
            {"label": "Рост", "value": "+81%"},
            {"label": "ЦА инвестиции", "value": "$12 млрд"},
            {"label": "Новые маршруты", "value": "3 ж/д"},
        ],
        "content": [
            {"type": "text", "body": "Инициатива «Один пояс, один путь» (BRI) продолжает масштабироваться, достигнув рекордных $128 млрд новых контрактов в 2024 году, что на 81% превышает показатели предыдущего года. При этом структура инвестиций претерпевает существенные изменения: фокус смещается от традиционной инфраструктуры к зелёным технологиям, цифровой экономике и устойчивому развитию."},
            {"type": "heading", "level": 2, "body": "Рекордный рост контрактов"},
            {"type": "text", "body": "Общий объём BRI-контрактов вырос на 81% и достиг рекордных $128 млрд в 2024 году, превзойдя даже пиковые показатели 2019 года. Рост обусловлен активизацией Китая в странах Глобального Юга, увеличением спроса на инфраструктуру в Центральной и Юго-Восточной Азии, а также запуском крупных проектов в секторе возобновляемой энергетики. Китай подписал 152 контракта стоимостью свыше $100 млн каждый, сосредоточив основные инвестиции в транспорте, энергетике и телекоммуникациях."},
            {"type": "chart_bar", "title": "Объём BRI-контрактов по годам ($ млрд)", "bars": [
                {"label": "2019", "value": 115, "max": 128, "display": "$115 млрд"},
                {"label": "2020", "value": 62, "max": 128, "display": "$62 млрд"},
                {"label": "2021", "value": 59, "max": 128, "display": "$59 млрд"},
                {"label": "2022", "value": 68, "max": 128, "display": "$68 млрд"},
                {"label": "2023", "value": 71, "max": 128, "display": "$71 млрд"},
                {"label": "2024", "value": 128, "max": 128, "display": "$128 млрд"},
            ]},
            {"type": "heading", "level": 2, "body": "Сдвиг к зелёным технологиям"},
            {"type": "text", "body": "Одна из наиболее заметных тенденций BRI 2024 — смещение приоритетов к зелёным технологиям. Доля «зелёных» контрактов выросла с 18% в 2022 году до 41% в 2024 году. Китайские компании активно экспортируют технологии EV-батарей, солнечных панелей и водородной энергетики. CATL строит гигафабрику аккумуляторов в Венгрии ($7.6 млрд), BYD открывает завод электромобилей в Узбекистане, а LONGi Solar возводит солнечные электростанции в Казахстане мощностью 1.5 ГВт."},
            {"type": "stats_grid", "items": [
                {"label": "BRI контракты", "value": "$128 млрд"},
                {"label": "Рост к 2023", "value": "+81%"},
                {"label": "ЦА инвестиции", "value": "$12 млрд"},
                {"label": "Зелёные проекты", "value": "41%"},
            ]},
            {"type": "heading", "level": 2, "body": "Центральная Азия: $12 млрд инвестиций"},
            {"type": "text", "body": "Центральная Азия получила $12 млрд инвестиций по линии BRI в 2024 году, что делает регион одним из приоритетных направлений китайской инвестиционной политики. Казахстан лидирует с $5.8 млрд (транспорт, энергетика, горнодобыча), за ним следуют Узбекистан ($3.2 млрд — автопром, текстиль, солнечная энергетика), Кыргызстан ($1.5 млрд — горнодобыча, ж/д инфраструктура) и Таджикистан ($1.1 млрд — ГЭС, автодороги). Особое значение имеют инвестиции в транспортную инфраструктуру, усиливающие позиции региона как транзитного хаба."},
            {"type": "heading", "level": 2, "body": "Три новых железнодорожных маршрута"},
            {"type": "text", "body": "В 2024 году запущены три новых железнодорожных маршрута из Синьцзяна через Казахстан: Урумчи–Хоргос–Алматы–Ташкент (контейнерный поезд, еженедельно), Кашгар–Иркештам–Бишкек (грузовой, два раза в неделю) и Хами–Достык–Актау–Баку (мультимодальный, через ТМТМ). Эти маршруты укрепляют сухопутное транспортное сообщение между Китаем и Европой, предлагая альтернативу перегруженным морским линиям. Суммарная пропускная способность новых маршрутов составляет 25 000 TEU ежемесячно."},
            {"type": "quote", "body": "BRI вступает в новую фазу — от количества к качеству. Зелёные технологии и цифровая инфраструктура определяют инвестиционные приоритеты нового Шёлкового пути.", "author": "Аналитический отдел TCC Hub"},
            {"type": "heading", "level": 2, "body": "Цифровой Шёлковый путь"},
            {"type": "text", "body": "Компонент Digital Silk Road набирает всё большее значение в структуре BRI. Инвестиции в дата-центры, 5G-инфраструктуру, облачные сервисы и системы электронного правительства в странах Центральной Азии составили $2.4 млрд в 2024 году. Huawei, ZTE и Alibaba Cloud открывают региональные хабы в Алматы и Ташкенте. Цифровой Шёлковый путь включает также прокладку оптоволоконных линий, связывающих Синьцзян с Ближним Востоком через Центральную Азию, и создание единого цифрового торгового пространства."},
            {"type": "list", "items": [
                "BRI-контракты достигли рекордных $128 млрд (+81%)",
                "41% новых контрактов приходится на зелёные технологии",
                "Центральная Азия получила $12 млрд — КЗ $5.8 млрд, УЗ $3.2 млрд",
                "Запущены 3 новых ж/д маршрута из Синьцзяна через Казахстан",
                "Цифровой Шёлковый путь: $2.4 млрд инвестиций в ИТ-инфраструктуру ЦА",
            ]},
        ],
    },
    "krasnoye-more-krizis": {
        "title": "Красное море: как кризис меняет глобальные маршруты",
        "slug": "krasnoye-more-krizis",
        "tag": "Экспертный отчёт · Санкционные риски",
        "date": "8 сентября 2024",
        "read_time": "10 мин",
        "image_url": "https://images.unsplash.com/photo-1524522173746-f628baad3644?w=1200&h=500&fit=crop",
        "meta_stats": [
            {"label": "Суэцкий канал", "value": "-90% трафика"},
            {"label": "Стоимость фрахта", "value": "x2.5"},
            {"label": "Заявки ТМТМ", "value": "+40%"},
            {"label": "Страховка", "value": "x10"},
        ],
        "content": [
            {"type": "text", "body": "Кризис в Красном море, спровоцированный атаками хуситов на торговые суда, стал крупнейшим потрясением для глобальной морской логистики со времён пандемии COVID-19. Падение трафика через Суэцкий канал на 90%, многократный рост стоимости фрахта и страхования радикально перераспределяют мировые грузопотоки в пользу альтернативных сухопутных коридоров."},
            {"type": "heading", "level": 2, "body": "Масштаб кризиса: Суэц потерял 90% трафика"},
            {"type": "text", "body": "С начала атак хуситов в ноябре 2023 года трафик через Суэцкий канал сократился на 90%, достигнув минимальных значений за последние 20 лет. Если в 2023 году через канал ежедневно проходило 70-80 судов, то к середине 2024 года этот показатель снизился до 5-8 судов в день. Администрация Суэцкого канала потеряла более $7 млрд доходов за первые девять месяцев 2024 года. Более 80% контейнерных линий официально перенаправили свои маршруты в обход мыса Доброй Надежды."},
            {"type": "chart_bar", "title": "Трафик Суэцкого канала: до и после кризиса (судов/день)", "bars": [
                {"label": "Янв 2023", "value": 78, "max": 82, "display": "78 судов/день"},
                {"label": "Июл 2023", "value": 82, "max": 82, "display": "82 судов/день"},
                {"label": "Янв 2024", "value": 25, "max": 82, "display": "25 судов/день"},
                {"label": "Апр 2024", "value": 12, "max": 82, "display": "12 судов/день"},
                {"label": "Июл 2024", "value": 8, "max": 82, "display": "8 судов/день"},
                {"label": "Сен 2024", "value": 6, "max": 82, "display": "6 судов/день"},
            ]},
            {"type": "heading", "level": 2, "body": "Обход мыса Доброй Надежды: +7-10 дней"},
            {"type": "text", "body": "Перенаправление судов вокруг Африки добавляет 7-10 дней к стандартному транзитному времени на маршруте Азия–Европа. Вместо 25-30 дней через Суэц, суда тратят 35-40 дней через мыс Доброй Надежды. Это не только увеличивает время доставки, но и существенно повышает расход топлива (+25-30%), что транслируется в стоимость фрахта. Дополнительные 6 000 морских миль маршрута создают эффект «бутылочного горлышка» в крупных африканских портах, особенно в Кейптауне и Дурбане, которые не рассчитаны на такой объём транзитного трафика."},
            {"type": "stats_grid", "items": [
                {"label": "Трафик Суэца", "value": "-90%"},
                {"label": "Стоимость фрахта", "value": "x2.5"},
                {"label": "Доп. время", "value": "+7-10 дней"},
                {"label": "Страховка", "value": "x10"},
            ]},
            {"type": "heading", "level": 2, "body": "Взрывной рост стоимости фрахта"},
            {"type": "text", "body": "Стоимость контейнерных перевозок Азия–Европа выросла в 2.5 раза по сравнению с докризисным уровнем. Ставка фрахта на 40-футовый контейнер (FEU) из Шанхая в Роттердам достигала $7,500-8,000 в пиковые месяцы, при докризисных $3,000-3,500. Рост обусловлен не только удлинением маршрута, но и дефицитом судоходных мощностей: суда, находящиеся на более длинных маршрутах, выпадают из оборота на дополнительные 7-10 дней, создавая нехватку тоннажа. Ожидается, что повышенные ставки сохранятся на протяжении всего 2025 года."},
            {"type": "heading", "level": 2, "body": "ТМТМ: всплеск спроса на +40%"},
            {"type": "text", "body": "Транскаспийский международный транспортный маршрут (ТМТМ) стал главным бенефициаром кризиса в Красном море. Число заявок на перевозку грузов по Среднему коридору выросло на 40% в 2024 году. Особенно заметен рост спроса со стороны производителей электроники и автокомпонентов, для которых критично время доставки. ТМТМ предлагает 12-15 дней транзита Китай–Европа, что вдвое быстрее морского маршрута через мыс Доброй Надежды. Узкие места — ограниченная пропускная способность каспийских портов и необходимость перестановки колёсных пар на границе."},
            {"type": "quote", "body": "Кризис в Красном море — не временное явление. Это структурный сдвиг, который фундаментально меняет глобальную логистику в пользу евразийских сухопутных коридоров.", "author": "Экспертный совет TCC Hub"},
            {"type": "heading", "level": 2, "body": "Страховые премии: десятикратный рост"},
            {"type": "text", "body": "Страховые премии для судов, проходящих через Красное море, выросли в 10 раз. Если до кризиса стандартная военная страховка составляла 0.01-0.05% от стоимости судна, то к середине 2024 года она достигла 0.5-1.0%. Для крупного контейнеровоза стоимостью $150 млн это означает дополнительные расходы в $750 тыс.–$1.5 млн за один проход. Несколько ведущих страховых компаний (Lloyd's, Swiss Re) включили Красное море в перечень зон высокого риска, фактически приравняв регион к зонам боевых действий."},
            {"type": "heading", "level": 2, "body": "Стратегическое преимущество альтернативных коридоров"},
            {"type": "text", "body": "Кризис создаёт окно стратегических возможностей для Среднего коридора и Северного морского пути. Средний коридор получает не только тактическое преимущество (перенаправление грузов), но и стратегическое: инвесторы и правительства ускоряют вложения в инфраструктуру, понимая, что зависимость от одного морского маршрута несёт неприемлемые риски. На горизонте 3-5 лет ожидается формирование мультимодальной сети коридоров с устойчивым перераспределением 15-20% евразийских грузопотоков на сухопутные маршруты."},
            {"type": "list", "items": [
                "Суэцкий канал потерял 90% трафика — минимум за 20 лет",
                "Обход через мыс Доброй Надежды: +7-10 дней и +25% расход топлива",
                "Контейнерный фрахт Азия–Европа вырос в 2.5 раза до $7,500-8,000/FEU",
                "ТМТМ: +40% заявок, 12-15 дней транзит Китай–Европа",
                "Страховые премии выросли в 10 раз, Красное море приравнено к зоне боевых действий",
                "Прогноз: 15-20% евразийских грузопотоков перейдут на сухопутные коридоры к 2029",
            ]},
        ],
    },
    "kazakhstan-shans-i-peregruzka-mart-2026": {
        "title": "Казахстан между шансом и перегрузкой",
        "slug": "kazakhstan-shans-i-peregruzka-mart-2026",
        "tag": "Аналитический обзор · Март 2026",
        "date": "Март 2026",
        "read_time": "15 мин",
        "image_url": "/static/img/tcc-article-cover.svg",
        "meta_stats": [
            {"label": "Транзит 2025", "value": "36.9 млн тонн"},
            {"label": "Рост ТМТМ", "value": "+36%"},
            {"label": "Морские перевозки", "value": "8 млн тонн"},
            {"label": "Контейнеры", "value": "90 637 TEU"},
        ],
        "content": [
            {"type": "text", "body": "Успеет ли транспортная система страны перестроиться раньше, чем перестроится сама Евразия?"},
            {"type": "text", "body": "Сегодня вопрос о роли Казахстана в евразийской логистике уже нельзя сводить к привычной формуле: «есть выгодная география, значит будет транзит». География дает стране стартовую позицию, но не гарантирует результат. В новой фазе мировой перестройки выигрывают не те, кто удачно расположен на карте, а те, кто умеет превращать свое положение в предсказуемую, связанную и управляемую транспортную систему. Именно здесь и проходит главная линия напряжения для Казахстана."},
            {"type": "text", "body": "Президент Касым-Жомарт Токаев на расширенном заседании Правительства 10 февраля 2026 года прямо обозначил, что в железнодорожно-логистическом контуре страны остаются высокий износ инфраструктуры, незавершенная цифровизация, необходимость полной оцифровки распределения вагонов, ускорения запуска Smart Cargo и Keden, а также принятия окончательного решения по новой тарифной политике до 1 сентября 2026 года. При этом Правительство сохраняет цель по доведению транзита до 55 млн тонн, хотя сама достижимость этой цели публично поставлена под вопрос."},
            {"type": "text", "body": "Проблема в том, что внешняя среда перестала быть фоном и стала фактором прямого давления на внутреннюю архитектуру маршрутов. Эскалация на Ближнем Востоке уже влияет на стоимость фрахта, страховые премии, топливо, доступность морских и воздушных плеч, а значит — меняет экономику поставок далеко за пределами региона."},
            {"type": "stats_grid", "items": [
                {"label": "Транзит 2025", "value": "36.9 млн т"},
                {"label": "Рост ТМТМ", "value": "+36%"},
                {"label": "Морские перевозки", "value": "8 млн т"},
                {"label": "Контейнеры", "value": "90 637 TEU"},
            ]},
            {"type": "heading", "level": 2, "body": "Главное противоречие 2026 года"},
            {"type": "text", "body": "Ключевое противоречие выглядит так: у Казахстана усиливается международное окно возможностей именно в тот момент, когда собственная транспортная система все еще находится в стадии внутренней донастройки. Это означает, что стране приходится одновременно решать две задачи, которые в идеальной ситуации решаются последовательно: сначала выстраивать внутреннюю управляемость, затем масштабировать внешнюю роль. Сейчас же делать это приходится параллельно. Такой режим всегда создает риск перегрева: спрос на коридор может расти быстрее, чем способность системы обеспечивать стабильный сервис."},
            {"type": "text", "body": "Из этого следует важный вывод: в 2026 году Казахстану нужно думать не просто о наращивании объемов, а о качестве отбора тех потоков, которые страна реально способна удержать. В условиях дорогого моря, нестабильного страхования и удлинения глобальных цепочек более ценными становятся не любые грузы, а те, что требуют скорости, предсказуемости, прозрачности и мультимодальной синхронизации."},
            {"type": "heading", "level": 2, "body": "Где проходит реальный контур риска"},
            {"type": "text", "body": "Слабое место Казахстана сегодня — не в отсутствии маршрута как такового. Маршрут есть. Слабое место — в разрывах между его элементами. Президентская критика как раз указывает на эти разрывы: отдельные инфраструктурные проекты движутся, цифровые решения существуют, модернизация границы идет, но единая система управления еще не завершена."},
            {"type": "text", "body": "Если смотреть стратегически, Казахстану уже недостаточно быть просто транзитной территорией между Китаем, Каспием, Кавказом и Европой. Ему нужно стать системой, которая умеет согласовывать интересы железной дороги, портов, автотранспортного плеча, терминалов и таможни; быстро приоритизировать грузовые потоки; давать рынку понятную тарифную логику; обеспечивать цифровую прослеживаемость и прогнозируемость сервиса."},
            {"type": "heading", "level": 2, "body": "Карта рисков: где Казахстан может потерять окно возможностей"},
            {"type": "list", "items": [
                "Тарифный риск — если тарифная политика останется затянутой или непрозрачной, грузы уйдут туда, где предсказуемость выше",
                "Риск узких мест в ж/д сети — высокий износ инфраструктуры, признанный на уровне Главы государства, может ограничить рост",
                "Риск фрагментированной мультимодальности — порты, ж/д, терминалы и автоплечо модернизируются по отдельности, но не дают единого сервиса",
                "Риск вагонной неадекватности — изменение товарной структуры транзита требует нового подхода к распределению вагонов",
                "Риск цифровой незавершенности — Smart Cargo и Keden в пилотном режиме, нужен ускоренный полноценный запуск",
                "Пограничный и таможенный риск — обновленная инфраструктура не решает проблему без интеграции с системами соседних стран",
                "Внешний геополитический риск — обострение на Ближнем Востоке создаёт одновременно шанс и угрозу",
            ]},
            {"type": "heading", "level": 2, "body": "Что Казахстану важно сделать прямо сейчас"},
            {"type": "text", "body": "Первое: перестать измерять успех только тоннами. Объем — важен, но в 2026 году куда важнее вопрос, какие именно грузы Казахстан способен не просто привлечь, а стабильно обслуживать с понятной экономикой и сервисом."},
            {"type": "text", "body": "Второе: перевести разговор о коридоре из языка инфраструктуры в язык операционной модели. Порты Актау и Курык, железная дорога, пункты пропуска, автоплечо и цифровые решения должны работать не как набор объектов, а как один сервисный контур."},
            {"type": "text", "body": "Третье: ускорить переход от пилотов к обязательной цифровой дисциплине. Пока цифровые платформы живут как проект, а не как отраслевой стандарт, коридор остается уязвимым."},
            {"type": "text", "body": "Четвертое: рассматривать Транскаспийский маршрут не как вспомогательное направление, а как пространство, где Казахстан может закрепить свою роль через сервисную надежность."},
            {"type": "text", "body": "Пятое: встроить risk management в саму архитектуру транспортной политики. В новой фазе мировой торговли выигрывает не самый дешевый маршрут, а тот, который умеет быстрее других адаптироваться к внешнему шоку."},
            {"type": "heading", "level": 2, "body": "5 лучших сценариев для Казахстана"},
            {"type": "list", "items": [
                "«Успели к окну возможностей» — тарифная модель принята до 1 сентября, Smart Cargo и Keden в полном запуске, Казахстан становится управляемым узлом Евразии",
                "«Премиальный транзит» — ставка на контейнерные, ускоренные, мультимодальные потоки, где важны предсказуемость и сервис, а не просто тоннаж",
                "«Каспийский усилитель» — Актау, Курык и флот работают как полноценный конкурентный морской сегмент коридора, а не приложение к ж/д",
                "«Цифровая прозрачность как преимущество» — полная цифровизация вагонов, границы, слотов превращает Казахстан в самый предсказуемый коридор",
                "«Транспорт как экономическая политика» — логистика встраивается в промышленную, инвестиционную и экспортную стратегию страны",
            ]},
            {"type": "heading", "level": 2, "body": "5 худших сценариев"},
            {"type": "list", "items": [
                "«Объем без управляемости» — транзит растет быстрее, чем способность системы его переварить: задержки, конфликт за мощности, потеря доверия рынка",
                "«Тарифная неопределенность» — рынок не получает ясной тарифной логики, грузы уходят туда, где предсказуемость выше",
                "«Пилоты вместо системы» — Smart Cargo и Keden остаются красивыми, но неполноценными решениями, ручное управление сохраняется",
                "«Каспий не справился» — порты, флот и стыковка с западным берегом не выдерживают ритм, железная дорога не превращается в устойчивый коридор",
                "«Мир перестроился быстрее» — глобальная логистика адаптируется, а Казахстан остается с незавершенной внутренней настройкой, теряя исторический темп",
            ]},
            {"type": "heading", "level": 2, "body": "Финальный вывод"},
            {"type": "text", "body": "Главный вопрос для Казахстана сегодня не в том, способен ли он стать логистическим центром Евразии. Потенциал для этого у страны есть. Настоящий вопрос другой: сумеет ли Казахстан за ограниченное время превратить транспортную систему из набора развивающихся элементов в единую модель управления потоком."},
            {"type": "quote", "body": "В 2026 году стране уже недостаточно иметь маршрут. Ей нужно доказать рынку, что этот маршрут можно планировать, просчитывать, страховать, бронировать и масштабировать без ощущения системной неопределенности.", "author": "TransCaspian Cargo"},
            {"type": "text", "body": "Если Казахстан справится с этой внутренней сборкой, он закрепит за собой не только транзит, но и влияние в новой архитектуре Евразии. Если нет — география останется преимуществом на бумаге, но не станет преимуществом в экономике."},
        ],
    },
}


def article_detail_view(request, slug):
    article = ARTICLES.get(slug)
    if not article:
        raise Http404("Статья не найдена")
    related = [a for s, a in ARTICLES.items() if s != slug][:3]
    return render(request, "site/article_detail.html", {
        "active_page": "analytics",
        "article": article,
        "related_articles": related,
    })


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next", "/dashboard/"))
        return render(request, "auth/login.html", {
            "form_errors": "Неверный email или пароль",
            "email": email,
        })
    return render(request, "auth/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        errors = []
        if not email or not username or not password:
            errors.append("Заполните все обязательные поля")
        if password != password_confirm:
            errors.append("Пароли не совпадают")
        if len(password) < 8:
            errors.append("Пароль должен содержать минимум 8 символов")
        if CustomUser.objects.filter(email=email).exists():
            errors.append("Пользователь с таким email уже существует")
        if CustomUser.objects.filter(username=username).exists():
            errors.append("Имя пользователя занято")

        if errors:
            return render(request, "auth/register.html", {
                "form_errors": " ".join(errors),
                "email": email,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            })

        user = CustomUser.objects.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        login(request, user)
        return redirect("dashboard")
    return render(request, "auth/register.html")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("landing")


# ──────────────────────────────────────────────
# Client cabinet
# ──────────────────────────────────────────────

@login_required
def dashboard_view(request):
    from apps.tcc_commerce.models import Order, ReportAccess
    reports_count = ReportAccess.objects.filter(user=request.user).count()
    orders_count = Order.objects.filter(user=request.user).count()
    return render(request, "dashboard/index.html", {
        "reports_count": reports_count,
        "orders_count": orders_count,
    })


@login_required
def profile_view(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        user.city = request.POST.get("city", user.city)
        user.country = request.POST.get("country", user.country)
        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]
        user.save()
        messages.success(request, "Профиль обновлён")
        return redirect("profile")
    return render(request, "dashboard/profile.html", {})


@login_required
@require_POST
def change_password_view(request):
    old_password = request.POST.get("old_password", "")
    new_password = request.POST.get("new_password", "")
    new_password_confirm = request.POST.get("new_password_confirm", "")

    if not request.user.check_password(old_password):
        messages.error(request, "Текущий пароль неверный")
        return redirect("profile")
    if new_password != new_password_confirm:
        messages.error(request, "Новые пароли не совпадают")
        return redirect("profile")
    if len(new_password) < 8:
        messages.error(request, "Пароль должен содержать минимум 8 символов")
        return redirect("profile")

    request.user.set_password(new_password)
    request.user.save()
    login(request, request.user)
    messages.success(request, "Пароль успешно изменён")
    return redirect("profile")


# ──────────────────────────────────────────────
# Reports catalog & commerce
# ──────────────────────────────────────────────

def reports_catalog_view(request):
    from apps.tcc_reports.models import Report, ReportTemplate
    reports = Report.objects.filter(status="published").select_related(
        "template", "created_by"
    ).prefetch_related("corridors")
    templates = ReportTemplate.objects.all()
    current_template = request.GET.get("template")
    if current_template:
        try:
            current_template = int(current_template)
            reports = reports.filter(template_id=current_template)
        except (ValueError, TypeError):
            current_template = None
    return render(request, "site/reports_catalog.html", {
        "reports": reports,
        "templates": templates,
        "current_template": current_template,
        "active_page": "reports",
    })


def report_detail_view(request, slug):
    from apps.tcc_reports.models import Report
    report = get_object_or_404(
        Report.objects.select_related("template", "created_by").prefetch_related(
            "corridors", "countries", "sections"
        ),
        slug=slug,
        status="published",
    )
    Report.objects.filter(pk=report.pk).update(views_count=report.views_count + 1)
    has_access = False
    if request.user.is_authenticated:
        has_access = (
            request.user.is_staff
            or report.accesses.filter(user=request.user).exists()
        )
    return render(request, "site/report_detail.html", {
        "report": report,
        "has_access": has_access,
        "active_page": "reports",
    })


@require_POST
@login_required
def buy_report_view(request, slug):
    from apps.tcc_commerce.models import Order, Product, ReportAccess
    from apps.tcc_reports.models import Report

    report = get_object_or_404(Report, slug=slug, status="published")
    if report.accesses.filter(user=request.user).exists():
        messages.info(request, "У вас уже есть доступ к этому отчёту")
        return redirect("report_detail", slug=slug)

    product = Product.objects.filter(report=report, is_active=True).first()
    if not product:
        product = Product.objects.create(
            product_type="single_report",
            name=report.title,
            description=f"Доступ к отчёту: {report.title}",
            price_usd=report.price_usd,
            report=report,
            is_active=True,
        )

    order = Order.objects.create(
        user=request.user,
        product=product,
        amount_usd=product.price_usd,
        status="pending",
    )

    if product.price_usd == 0:
        order.status = "paid"
        order.paid_at = timezone.now()
        order.save()
        ReportAccess.objects.get_or_create(
            user=request.user,
            report=report,
            defaults={"order": order, "access_type": "free"},
        )
        messages.success(request, "Доступ получен!")
        return redirect("report_detail", slug=slug)

    order.status = "paid"
    order.paid_at = timezone.now()
    order.payment_ref = f"SIM-{order.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    order.save()
    ReportAccess.objects.get_or_create(
        user=request.user,
        report=report,
        defaults={"order": order, "access_type": "purchase"},
    )
    messages.success(request, "Оплата прошла успешно! Доступ к отчёту открыт.")
    return redirect("report_detail", slug=slug)


@login_required
def dashboard_my_reports_view(request):
    from apps.tcc_reports.models import Report
    # Show user's own generated reports
    my_reports = Report.objects.filter(
        created_by=request.user
    ).select_related("template").order_by("-created_at")
    # For admin: show all reports
    all_reports = None
    if request.user.is_staff:
        all_reports = Report.objects.select_related(
            "template", "created_by"
        ).order_by("-created_at")
    return render(request, "dashboard/my_reports.html", {
        "my_reports": my_reports,
        "all_reports": all_reports,
        "active_page": "my_reports",
    })


@login_required
def dashboard_my_orders_view(request):
    from apps.tcc_commerce.models import Order
    orders = Order.objects.filter(
        user=request.user
    ).select_related("product")
    return render(request, "dashboard/my_orders.html", {
        "orders": orders,
        "active_page": "my_orders",
    })


# ──────────────────────────────────────────────
# CMS Editor (admin-only, inside dashboard)
# ──────────────────────────────────────────────
# Security:
#   - All views gated by _staff_required (is_authenticated + is_staff).
#   - POST is CSRF-protected by Django's middleware.
#   - Input lengths are clamped server-side to prevent DoS/abuse via huge payloads.
#   - Field values are auto-escaped by Django templates (no XSS).
#     Exception: cms_html renders `body` via mark_safe — admin users are trusted
#     to enter HTML in that field (same trust model as Wagtail / WordPress).
#   - CMS mutations are logged for audit.
import logging

from django.contrib.auth.decorators import user_passes_test

from apps.landing.models import Page, PageSection

cms_logger = logging.getLogger("tcchub.cms")

_staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff)

# Input length limits (chars). Matches model field limits + sanity cap on body.
_CMS_LIMITS = {
    "title": 200,
    "meta_title": 200,
    "meta_description": 500,
    "eyebrow": 120,
    "heading": 300,
    "subheading": 500,
    "body": 20000,
    "cta_label": 120,
    "cta_url": 500,
}


def _clean(request_post, key, limit):
    """Strip + length-clamp a POST field."""
    value = (request_post.get(key) or "").strip()
    if len(value) > limit:
        value = value[:limit]
    return value


# Expected PageSection keys per page slug — ensures editor always shows the full
# block list even if DB rows were never seeded. Order matches visual order on page.
# Per-page block manifest with default text.
# Format: (section_key, eyebrow, heading, subheading)
# Used by _ensure_sections to: (a) create missing rows, (b) backfill empty
# fields on existing rows so the editor shows current text for editing.
_CMS_PAGE_MANIFEST = {
    "landing": [
        ("hero", "Eurasia · TMTM · BRI", "TransCaspian Cargo",
         "Экосистема бизнес-решений в логистике и цепях поставок"),
        ("intro", "Манифест", "Мировая торговля переживает структурную трансформацию.",
         "— подход TransCaspian Cargo"),
        ("features", "Контекст 2026", "Почему TCC актуален именно сейчас",
         "Три структурных сдвига последних лет изменили правила игры в логистике. Игнорировать их — значит проигрывать ещё до начала проекта."),
        ("stats", "Средний коридор", "Транскаспийский маршрут ТМТМ",
         "Средний коридор становится одним из ключевых маршрутов между Европой и Азией. TransCaspian Cargo участвует в развитии экспертной и проектной инфраструктуры этого направления."),
        ("services", "Последние исследования", "Экспертные материалы", ""),
        ("cases", "Наши клиенты и партнёры", "Экосистема партнёрств TCC",
         "Логистические компании, университеты, отраслевые ассоциации, промышленные группы и международные организации"),
        ("testimonials", "Юридическая легитимность", "Платформа с подтверждённым правовым статусом",
         "TCC — официально зарегистрированная организация Республики Казахстан с международной аккредитацией и патентом на собственную технологическую платформу."),
        ("cta", "Сотрудничество", "Стать партнёром TransCaspian Cargo",
         "Присоединяйтесь к экосистеме отраслевой экспертизы в логистике Евразии"),
    ],
    "about": [
        ("hero", "О платформе", "TransCaspian Cargo",
         "Экосистема стратегических решений для бизнеса, инвесторов, институтов развития и государственных структур — на пересечении логистики, аналитики и образования"),
        ("section_1", "О компании", "История создания TransCaspian Cargo",
         "TCC — это экосистема стратегических решений для бизнеса, инвесторов, институтов развития и государственных структур. TCC работает там, где пересекаются логистика, аналитика, стратегия, экспертиза, образование и международное сотрудничество."),
        ("section_2", "Миссия", "Формирование устойчивой логистической инфраструктуры Евразии",
         "Повышать качество стратегического управления в логистике и инфраструктуре, снижать риски, усиливать устойчивость проектов и укреплять капитал компаний через более зрелые цепи поставок, сильные управленческие решения и развитие профессиональной среды."),
        ("section_3", "Видение", "Ключевая интеллектуальная и практическая платформа Евразии в области логистики",
         "TCC стремится стать одной из ключевых интеллектуальных и практических платформ Евразии в области логистики, supply chain management, транспортных коридоров и профессионального развития отрасли."),
        ("section_4", "Экосистема TCC", "Ключевые направления платформы",
         "Каждое направление усиливает остальные, формируя единую экосистему, где знания превращаются в инструменты, инструменты — в решения, а решения — в устойчивые результаты."),
        ("section_5", "Команда", "Эксперты и партнёры",
         "Практики с многолетним опытом в логистике, транспорте и цепях поставок"),
        ("section_6", "", "Присоединяйтесь к экосистеме TCC",
         "Станьте частью платформы отраслевой экспертизы в логистике Евразии"),
    ],
    "analytics": [
        ("hero", "Аналитика TCC", "Глубокая экспертиза рынка и точные данные",
         "Комплексные исследования логистики и инфраструктуры Центральной Азии, торговых коридоров Евразии и геоэкономических трендов для стратегических решений бизнеса."),
        ("cta", "", "Получайте аналитику первыми",
         "Подпишитесь на еженедельный дайджест TCC с экспертными материалами"),
    ],
    "reports": [
        ("hero", "Аналитика TCC", "Аналитические отчёты торговых коридоров",
         "Экспертный анализ цепей поставок Евразии: риск-скоры, санкционный скрининг, сценарии развития коридоров и матрицы решений для бизнеса."),
    ],
    "solutions": [
        ("hero", "Решения для бизнеса", "Стратегическое сопровождение бизнеса",
         "TCC помогает организациям анализировать цепи поставок, выявлять уязвимости, находить устойчивые маршруты и адаптироваться к быстро меняющимся условиям логистики Евразии."),
        ("section_2", "", "Направления практической работы TCC",
         "От стратегии до выхода на новые рынки — комплексное сопровождение бизнеса"),
        ("section_3", "", "Как мы работаем",
         "Четыре этапа от первичной диагностики до внедрения решений"),
        ("cta", "", "Запросить стратегическую сессию",
         "Получите экспертную оценку ваших цепей поставок и моделирование сценариев от специалистов TCC"),
    ],
    "projects": [
        ("hero", "Отраслевые проекты", "Инициативы, которые меняют логистику Евразии",
         "Проекты TCC объединяют экспертизу, аналитику и партнёрство для развития Среднего коридора, международных перевозок и исследовательских программ."),
        ("cta", "", "Стать участником проекта",
         "Присоединяйтесь к отраслевым инициативам TransCaspian Cargo"),
    ],
    "partners": [
        ("hero", "Сеть партнёров", "Партнёры, которые усиливают экосистему",
         "Международные организации, университеты и отраслевые объединения, с которыми TCC строит долгосрочные стратегические партнёрства в логистике, образовании и аналитике."),
        ("section_2", "", "Международные организации", ""),
        ("section_3", "", "Образовательные институты", ""),
        ("cta", "", "Стать партнёром TransCaspian Cargo",
         "Присоединяйтесь к экосистеме отраслевой экспертизы в логистике Евразии"),
    ],
    "education": [
        ("hero", "Образование TCC", "Развитие профессиональных компетенций",
         "Образовательные программы, executive-форматы и партнёрства с университетами для специалистов логистики, supply chain и стратегического управления."),
        ("section_2", "", "Форматы обучения",
         "Образовательные программы, практикумы и корпоративное обучение"),
        ("section_3", "", "Тематические направления",
         "Ключевые области знаний для специалиста нового типа"),
        ("section_courses", "", "Авторские программы обучения",
         "От практиков отрасли с многолетним опытом"),
        ("section_4", "", "Эксперты программ",
         "Практики отрасли с многолетним опытом"),
        ("cta", "", "Развивайте компетенции с TCC",
         "Эволюция требований к специалисту в логистике отражает трансформацию самой экономики"),
    ],
    "media": [
        ("hero", "Медиа TCC", "Экспертный контент отрасли",
         "Статьи, интервью, исследования и видео — всё, что формирует профессиональный взгляд на логистику Евразии и развитие торговых коридоров."),
        ("cta", "", "Подписывайтесь на наш Telegram",
         "Оперативные новости, аналитика и обсуждения с экспертами отрасли"),
    ],
    "contacts": [
        ("hero", "Связь с TCC", "Поговорим о вашем проекте",
         "Получите бесплатную консультацию от экспертов TCC по управлению цепями поставок, логистике Евразии и стратегическому развитию."),
        ("form", "— Заполните форму", "Расскажите о задаче",
         "Опишите вашу задачу — мы свяжемся в ближайшее время и предложим варианты решения от наших экспертов."),
    ],
    "wiki": [
        ("hero", "Справочник логиста", "WikiЛогист — энциклопедия логистики",
         "270+ терминов · Законы РК · Документы · Конвенции · Ресурсы"),
    ],
}


def _ensure_sections(page):
    """Create missing PageSection rows AND backfill empty fields from manifest
    defaults, so the editor always shows current text for editing."""
    manifest = _CMS_PAGE_MANIFEST.get(page.slug)
    if not manifest:
        return
    existing = {s.section_key: s for s in page.sections.all()}
    for order, row in enumerate(manifest, start=1):
        key, eyebrow, heading, subheading = row
        section = existing.get(key)
        if section is None:
            PageSection.objects.create(
                page=page,
                section_key=key,
                order=order,
                is_visible=True,
                eyebrow=eyebrow,
                heading=heading,
                subheading=subheading,
            )
            continue
        # Backfill only empty fields — never overwrite admin edits.
        changed = False
        if not section.eyebrow and eyebrow:
            section.eyebrow = eyebrow
            changed = True
        if not section.heading and heading:
            section.heading = heading
            changed = True
        if not section.subheading and subheading:
            section.subheading = subheading
            changed = True
        if changed:
            section.save(update_fields=["eyebrow", "heading", "subheading"])


@_staff_required
def dashboard_cms_list(request):
    pages = Page.objects.all().order_by("title").prefetch_related("sections")
    return render(request, "dashboard/cms_list.html", {"pages": pages})


@_staff_required
def dashboard_cms_page(request, slug):
    page = get_object_or_404(Page, slug=slug)
    _ensure_sections(page)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save_page":
            page.title = _clean(request.POST, "title", _CMS_LIMITS["title"]) or page.title
            page.meta_title = _clean(request.POST, "meta_title", _CMS_LIMITS["meta_title"])
            page.meta_description = _clean(request.POST, "meta_description", _CMS_LIMITS["meta_description"])
            page.save()
            cms_logger.info("cms.page.save user=%s slug=%s", request.user.pk, slug)
            messages.success(request, "Страница сохранена")
            return redirect("dashboard_cms_page", slug=slug)
        if action == "save_sections":
            changed = 0
            for section in page.sections.all():
                prefix = f"sec_{section.id}_"
                section.is_visible = bool(request.POST.get(prefix + "is_visible"))
                section.eyebrow = _clean(request.POST, prefix + "eyebrow", _CMS_LIMITS["eyebrow"])
                section.heading = _clean(request.POST, prefix + "heading", _CMS_LIMITS["heading"])
                section.subheading = _clean(request.POST, prefix + "subheading", _CMS_LIMITS["subheading"])
                section.body = _clean(request.POST, prefix + "body", _CMS_LIMITS["body"])
                section.cta_label = _clean(request.POST, prefix + "cta_label", _CMS_LIMITS["cta_label"])
                section.cta_url = _clean(request.POST, prefix + "cta_url", _CMS_LIMITS["cta_url"])
                section.save()
                changed += 1
            cms_logger.info("cms.sections.save user=%s slug=%s count=%d", request.user.pk, slug, changed)
            messages.success(request, "Блоки сохранены")
            return redirect("dashboard_cms_page", slug=slug)
    sections = page.sections.all().order_by("order", "id")
    return render(request, "dashboard/cms_page.html", {"page": page, "sections": sections})


@_staff_required
@require_POST
def dashboard_cms_toggle(request, section_id):
    s = get_object_or_404(PageSection, id=section_id)
    s.is_visible = not s.is_visible
    s.save(update_fields=["is_visible"])
    cms_logger.info("cms.section.toggle user=%s section=%d visible=%s",
                    request.user.pk, s.id, s.is_visible)
    return redirect("dashboard_cms_page", slug=s.page.slug)


@_staff_required
def dashboard_cms_help(request):
    return render(request, "dashboard/cms_help.html", {})


DEVELOPER_EMAIL = "kairov.a@apec.edu.kz"


@_staff_required
@require_POST
def dashboard_cms_request(request):
    """Send change request email to the developer."""
    from django.core.mail import send_mail
    from django.conf import settings

    page_slug = _clean(request.POST, "page_slug", 80)
    section_key = _clean(request.POST, "section_key", 80)
    message = _clean(request.POST, "message", 5000)
    if not message:
        messages.error(request, "Опишите, что нужно изменить")
        return redirect(request.META.get("HTTP_REFERER") or "dashboard_cms_list")

    user = request.user
    subject = f"[TCC Hub CMS] Запрос на изменение: /{page_slug or '—'}"
    body = (
        f"От: {user.get_full_name() or user.username} <{user.email or '—'}>\n"
        f"Страница: /{page_slug}\n"
        f"Блок: {section_key or '—'}\n\n"
        f"Сообщение:\n{message}\n"
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [DEVELOPER_EMAIL],
            fail_silently=False,
        )
        cms_logger.info("cms.request.sent user=%s slug=%s", user.pk, page_slug)
        messages.success(request, "Запрос отправлен разработчику")
    except Exception as e:
        cms_logger.error("cms.request.failed user=%s err=%s", user.pk, e)
        messages.error(request, f"Не удалось отправить: {e}")

    if page_slug:
        return redirect("dashboard_cms_page", slug=page_slug)
    return redirect("dashboard_cms_list")


# ──────────────────────────────────────────────
# CMS · SiteNews CRUD (news editor)
# ──────────────────────────────────────────────
from apps.landing.models import SiteNews
from datetime import date as _date


def _parse_date(val, default=None):
    from datetime import datetime
    if not val:
        return default or _date.today()
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        return default or _date.today()


@_staff_required
def dashboard_cms_news_list(request):
    news = SiteNews.objects.all()
    return render(request, "dashboard/cms_news_list.html", {
        "news": news,
        "active_page": "cms",
    })


@_staff_required
def dashboard_cms_news_edit(request, news_id=None):
    item = None
    if news_id:
        item = SiteNews.objects.filter(pk=news_id).first()
        if not item:
            messages.error(request, "Новость не найдена")
            return redirect("dashboard_cms_news_list")

    if request.method == "POST":
        title = _clean(request.POST, "title", 300)
        if not title:
            messages.error(request, "Заголовок обязателен")
            return redirect(request.path)

        kind = _clean(request.POST, "kind", 32) or "новость"
        valid_kinds = {k for k, _ in SiteNews.TYPE_CHOICES}
        if kind not in valid_kinds:
            kind = "новость"

        excerpt = _clean(request.POST, "excerpt", 600)
        body = request.POST.get("body", "")[:20000]
        cover_url = _clean(request.POST, "cover_url", 1000)
        external_url = _clean(request.POST, "external_url", 1000)
        published_at = _parse_date(request.POST.get("published_at"))
        is_published = bool(request.POST.get("is_published"))
        show_on_landing = bool(request.POST.get("show_on_landing"))
        try:
            order = int(request.POST.get("order") or 0)
        except ValueError:
            order = 0

        if item is None:
            item = SiteNews()
        item.title = title
        item.kind = kind
        item.excerpt = excerpt
        item.body = body
        item.cover_url = cover_url
        item.external_url = external_url
        item.published_at = published_at
        item.is_published = is_published
        item.show_on_landing = show_on_landing
        item.order = order
        if request.FILES.get("cover"):
            item.cover = request.FILES["cover"]
        item.save()
        cms_logger.info("cms.news.save user=%s id=%s", request.user.pk, item.pk)
        messages.success(request, "Новость сохранена")
        return redirect("dashboard_cms_news_edit", news_id=item.pk)

    return render(request, "dashboard/cms_news_edit.html", {
        "item": item,
        "kinds": SiteNews.TYPE_CHOICES,
        "active_page": "cms",
    })


# ──────────────────────────────────────────────
# CMS · SiteItem CRUD (articles/partners/projects/programs/reports/team)
# ──────────────────────────────────────────────
from apps.landing.models import SiteItem

_CATEGORY_LABELS = dict(SiteItem.CATEGORY_CHOICES)

_CATEGORY_SUBCATS = {
    "partner": [("international", "Международные"), ("education", "Образование")],
    "project": [("middle_corridor", "Средний коридор"),
                ("international", "Международные"),
                ("research", "Исследования")],
}


@_staff_required
def dashboard_cms_items_list(request, category):
    if category not in _CATEGORY_LABELS:
        messages.error(request, "Неизвестная категория")
        return redirect("dashboard_cms_list")
    items = SiteItem.objects.filter(category=category)
    return render(request, "dashboard/cms_items_list.html", {
        "items": items,
        "category": category,
        "category_label": _CATEGORY_LABELS[category],
        "active_page": "cms",
    })


@_staff_required
def dashboard_cms_items_edit(request, category, item_id=None):
    if category not in _CATEGORY_LABELS:
        messages.error(request, "Неизвестная категория")
        return redirect("dashboard_cms_list")

    item = None
    if item_id:
        item = SiteItem.objects.filter(pk=item_id, category=category).first()
        if not item:
            messages.error(request, "Элемент не найден")
            return redirect("dashboard_cms_items_list", category=category)

    if request.method == "POST":
        title = _clean(request.POST, "title", 300)
        if not title:
            messages.error(request, "Заголовок обязателен")
            return redirect(request.path)

        if item is None:
            item = SiteItem(category=category)
        item.title = title
        item.subtitle = _clean(request.POST, "subtitle", 300)
        item.subcategory = _clean(request.POST, "subcategory", 80)
        item.slug = _clean(request.POST, "slug", 200)
        item.description = _clean(request.POST, "description", 1500)
        item.body = request.POST.get("body", "")[:30000]
        item.image_url = _clean(request.POST, "image_url", 1000)
        item.link_url = _clean(request.POST, "link_url", 1000)
        item.tag = _clean(request.POST, "tag", 80)
        item.status = _clean(request.POST, "status", 40)
        item.is_published = bool(request.POST.get("is_published"))
        try:
            item.order = int(request.POST.get("order") or 0)
        except ValueError:
            item.order = 0
        # metrics
        metrics_raw = _clean(request.POST, "metrics", 500)
        if metrics_raw:
            item.data = dict(item.data or {})
            item.data["metrics"] = [m.strip() for m in metrics_raw.split("|") if m.strip()]
        if request.FILES.get("image"):
            item.image = request.FILES["image"]
        item.save()
        cms_logger.info("cms.item.save user=%s cat=%s id=%s",
                        request.user.pk, category, item.pk)
        messages.success(request, "Сохранено")
        return redirect("dashboard_cms_items_edit", category=category, item_id=item.pk)

    return render(request, "dashboard/cms_items_edit.html", {
        "item": item,
        "category": category,
        "category_label": _CATEGORY_LABELS[category],
        "subcats": _CATEGORY_SUBCATS.get(category, []),
        "active_page": "cms",
    })


@_staff_required
@require_POST
def dashboard_cms_items_delete(request, category, item_id):
    item = SiteItem.objects.filter(pk=item_id, category=category).first()
    if item:
        item.delete()
        cms_logger.info("cms.item.delete user=%s cat=%s id=%s",
                        request.user.pk, category, item_id)
        messages.success(request, "Удалено")
    return redirect("dashboard_cms_items_list", category=category)


@_staff_required
@require_POST
def dashboard_cms_news_delete(request, news_id):
    item = SiteNews.objects.filter(pk=news_id).first()
    if item:
        item.delete()
        cms_logger.info("cms.news.delete user=%s id=%s", request.user.pk, news_id)
        messages.success(request, "Новость удалена")
    return redirect("dashboard_cms_news_list")


# ──────────────────────────────────────────────
# Dashboard · Заявки (contact submissions)
# ──────────────────────────────────────────────

@_staff_required
def dashboard_submissions_list(request):
    subs = ContactSubmission.objects.all()[:100]
    unread = [s.pk for s in subs if not s.is_read]
    if unread:
        ContactSubmission.objects.filter(pk__in=unread).update(is_read=True)
    return render(request, "dashboard/submissions_list.html", {"submissions": subs})
