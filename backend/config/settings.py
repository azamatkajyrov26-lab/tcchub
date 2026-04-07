import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
for _h in ("89.207.255.107.sslip.io", "89.207.255.107"):
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
    # Local apps
    "apps.web",
    "apps.accounts",
    "apps.courses",
    "apps.content",
    "apps.quizzes",
    "apps.assignments",
    "apps.grades",
    "apps.forums",
    "apps.notifications",
    "apps.messaging",
    "apps.certificates",
    "apps.badges",
    "apps.calendar",
    "apps.analytics",
    "apps.landing",
    # TCC Analytics Platform
    "apps.tcc_core",
    "apps.tcc_data",
    "apps.tcc_intelligence",
    "apps.tcc_emulator",
    "apps.tcc_reports",
    "apps.tcc_commerce",
    "apps.tcc_alerts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "tcchub"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.CustomUser"

LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Aqtau"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", BASE_DIR / "staticfiles")

MEDIA_URL = "media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

# --- SimpleJWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# --- Celery ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "sync-ofac-daily": {
        "task": "apps.tcc_data.tasks.sync_ofac_sanctions",
        "schedule": 86400,  # 24 hours
    },
    "sync-eu-sanctions-daily": {
        "task": "apps.tcc_data.tasks.sync_eu_sanctions",
        "schedule": 86400,
    },
    "sync-un-sanctions-daily": {
        "task": "apps.tcc_data.tasks.sync_un_sanctions",
        "schedule": 86400,
    },
    "sync-worldbank-weekly": {
        "task": "apps.tcc_data.tasks.sync_worldbank_indicators",
        "schedule": 604800,  # 7 days
    },
    "parse-news-2h": {
        "task": "apps.tcc_data.tasks.parse_and_annotate_news",
        "schedule": 7200,  # 2 hours
    },
    "recalculate-scores-6h": {
        "task": "apps.tcc_intelligence.tasks.recalculate_all_route_scores",
        "schedule": 21600,  # 6 hours
    },
    "update-emulated-daily": {
        "task": "apps.tcc_emulator.tasks.update_emulated_data",
        "schedule": 86400,
    },
    "check-alerts-hourly": {
        "task": "apps.tcc_alerts.tasks.check_and_generate_alerts",
        "schedule": 3600,  # 1 hour
    },
}

# --- drf-spectacular ---
SPECTACULAR_SETTINGS = {
    "TITLE": "TCC HUB LMS API",
    "DESCRIPTION": "TransCaspian Cargo Learning Management System API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
}

# --- Email ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@tcchub.kz")

# --- File upload limits ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# --- Auth redirects ---
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# --- Unfold Admin Theme ---
UNFOLD = {
    "SITE_TITLE": "TCC HUB",
    "SITE_HEADER": "TCC HUB Admin",
    "SITE_SYMBOL": "school",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "dark",
    "COLORS": {
        "primary": {
            "50": "#fdf8ef",
            "100": "#f9ecd4",
            "200": "#f2d6a8",
            "300": "#e8c07d",
            "400": "#d6b37b",
            "500": "#c9a05a",
            "600": "#b8944f",
            "700": "#997741",
            "800": "#7d613b",
            "900": "#665033",
            "950": "#362a19",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Навигация",
                "separator": True,
                "items": [
                    {
                        "title": "Панель управления",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                ],
            },
            {
                "title": "Обучение",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Категории",
                        "icon": "category",
                        "link": "/admin/courses/category/",
                    },
                    {
                        "title": "Курсы",
                        "icon": "menu_book",
                        "link": "/admin/courses/course/",
                    },
                    {
                        "title": "Секции / Модули",
                        "icon": "view_list",
                        "link": "/admin/courses/section/",
                    },
                    {
                        "title": "Активности",
                        "icon": "assignment",
                        "link": "/admin/content/activity/",
                    },
                    {
                        "title": "Ресурсы / Файлы",
                        "icon": "attach_file",
                        "link": "/admin/content/resource/",
                    },
                    {
                        "title": "Папки",
                        "icon": "folder",
                        "link": "/admin/content/folder/",
                    },
                ],
            },
            {
                "title": "Оценивание",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Тесты",
                        "icon": "quiz",
                        "link": "/admin/quizzes/quiz/",
                    },
                    {
                        "title": "Вопросы",
                        "icon": "help_outline",
                        "link": "/admin/quizzes/question/",
                    },
                    {
                        "title": "Задания",
                        "icon": "task",
                        "link": "/admin/assignments/assignment/",
                    },
                    {
                        "title": "Работы студентов",
                        "icon": "upload_file",
                        "link": "/admin/assignments/submission/",
                    },
                    {
                        "title": "Журнал оценок",
                        "icon": "grade",
                        "link": "/admin/grades/grade/",
                    },
                ],
            },
            {
                "title": "Коммуникации",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Форумы",
                        "icon": "forum",
                        "link": "/admin/forums/forum/",
                    },
                    {
                        "title": "Сообщения",
                        "icon": "chat",
                        "link": "/admin/messaging/message/",
                    },
                    {
                        "title": "Уведомления",
                        "icon": "notifications",
                        "link": "/admin/notifications/notification/",
                    },
                ],
            },
            {
                "title": "Достижения",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Сертификаты",
                        "icon": "workspace_premium",
                        "link": "/admin/certificates/issuedcertificate/",
                    },
                    {
                        "title": "Шаблоны сертификатов",
                        "icon": "description",
                        "link": "/admin/certificates/certificatetemplate/",
                    },
                    {
                        "title": "Значки",
                        "icon": "military_tech",
                        "link": "/admin/badges/badge/",
                    },
                ],
            },
            {
                "title": "Пользователи",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Пользователи",
                        "icon": "people",
                        "link": "/admin/accounts/customuser/",
                    },
                    {
                        "title": "Записи на курсы",
                        "icon": "how_to_reg",
                        "link": "/admin/courses/enrollment/",
                    },
                    {
                        "title": "Группы",
                        "icon": "groups",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": "Лендинг",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Hero секция",
                        "icon": "web",
                        "link": "/admin/landing/herosection/",
                    },
                    {
                        "title": "Метрики",
                        "icon": "bar_chart",
                        "link": "/admin/landing/metric/",
                    },
                    {
                        "title": "Партнёры",
                        "icon": "handshake",
                        "link": "/admin/landing/partner/",
                    },
                    {
                        "title": "Отзывы",
                        "icon": "rate_review",
                        "link": "/admin/landing/testimonial/",
                    },
                    {
                        "title": "Преимущества",
                        "icon": "star",
                        "link": "/admin/landing/advantage/",
                    },
                    {
                        "title": "Контакты",
                        "icon": "contact_page",
                        "link": "/admin/landing/contactinfo/",
                    },
                ],
            },
            {
                "title": "TCC Платформа",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Коридоры",
                        "icon": "route",
                        "link": "/admin/tcc_core/tradecorridor/",
                    },
                    {
                        "title": "Узлы маршрутов",
                        "icon": "location_on",
                        "link": "/admin/tcc_core/routenode/",
                    },
                    {
                        "title": "Страны",
                        "icon": "flag",
                        "link": "/admin/tcc_core/country/",
                    },
                    {
                        "title": "Регионы",
                        "icon": "public",
                        "link": "/admin/tcc_core/region/",
                    },
                    {
                        "title": "Источники данных",
                        "icon": "cloud_sync",
                        "link": "/admin/tcc_data/datasource/",
                    },
                    {
                        "title": "Санкционные списки",
                        "icon": "gavel",
                        "link": "/admin/tcc_data/sanctionentry/",
                    },
                    {
                        "title": "Логи синхронизации",
                        "icon": "sync",
                        "link": "/admin/tcc_data/synclog/",
                    },
                    {
                        "title": "Торговые потоки",
                        "icon": "swap_horiz",
                        "link": "/admin/tcc_data/tradeflow/",
                    },
                    {
                        "title": "Новости",
                        "icon": "newspaper",
                        "link": "/admin/tcc_data/newsitem/",
                    },
                    {
                        "title": "Риск-факторы",
                        "icon": "warning",
                        "link": "/admin/tcc_intelligence/riskfactor/",
                    },
                    {
                        "title": "Скоры маршрутов",
                        "icon": "speed",
                        "link": "/admin/tcc_intelligence/routescore/",
                    },
                    {
                        "title": "Сценарии",
                        "icon": "alt_route",
                        "link": "/admin/tcc_intelligence/scenario/",
                    },
                    {
                        "title": "Эмуляторы",
                        "icon": "science",
                        "link": "/admin/tcc_emulator/emulateddatasource/",
                    },
                    {
                        "title": "Шаблоны отчётов",
                        "icon": "description",
                        "link": "/admin/tcc_reports/reporttemplate/",
                    },
                    {
                        "title": "Отчёты",
                        "icon": "article",
                        "link": "/admin/tcc_reports/report/",
                    },
                    {
                        "title": "Продукты",
                        "icon": "shopping_cart",
                        "link": "/admin/tcc_commerce/product/",
                    },
                    {
                        "title": "Заказы",
                        "icon": "receipt_long",
                        "link": "/admin/tcc_commerce/order/",
                    },
                    {
                        "title": "Доступы к отчётам",
                        "icon": "key",
                        "link": "/admin/tcc_commerce/reportaccess/",
                    },
                    {
                        "title": "Оповещения",
                        "icon": "campaign",
                        "link": "/admin/tcc_alerts/alert/",
                    },
                    {
                        "title": "Подписки на оповещения",
                        "icon": "notifications_active",
                        "link": "/admin/tcc_alerts/alertsubscription/",
                    },
                ],
            },
            {
                "title": "Аналитика",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Действия пользователей",
                        "icon": "analytics",
                        "link": "/admin/analytics/useractivity/",
                    },
                    {
                        "title": "Отчёты по курсам",
                        "icon": "assessment",
                        "link": "/admin/analytics/coursereport/",
                    },
                    {
                        "title": "Логи входов",
                        "icon": "login",
                        "link": "/admin/analytics/loginlog/",
                    },
                    {
                        "title": "Календарь",
                        "icon": "calendar_month",
                        "link": "/admin/calendar/event/",
                    },
                ],
            },
        ],
    },
}


# ─── Production Security (active when DEBUG=False) ───
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://89.207.255.107.sslip.io,http://89.207.255.107.sslip.io"
    ).split(",") if o.strip()
]
for _o in ("https://89.207.255.107.sslip.io", "http://89.207.255.107.sslip.io"):
    if _o not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_o)

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in ("true", "1")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False
