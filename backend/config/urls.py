from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Web frontend (Django templates + HTMX)
    path("", include("apps.web.urls")),
    # API v1
    path("api/v1/accounts/", include("apps.accounts.urls", namespace="accounts_api")),
    path("api/v1/courses/", include("apps.courses.urls")),
    path("api/v1/content/", include("apps.content.urls")),
    path("api/v1/quizzes/", include("apps.quizzes.urls")),
    path("api/v1/assignments/", include("apps.assignments.urls")),
    path("api/v1/grades/", include("apps.grades.urls")),
    path("api/v1/forums/", include("apps.forums.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/messaging/", include("apps.messaging.urls")),
    path("api/v1/certificates/", include("apps.certificates.urls")),
    path("api/v1/badges/", include("apps.badges.urls")),
    path("api/v1/calendar/", include("apps.calendar.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/landing/", include("apps.landing.urls")),
    path("site-admin/content/", include("apps.landing.admin_urls")),
    # TCC Analytics Platform
    path("api/v1/tcc/", include("apps.tcc_core.urls")),
    path("api/v1/tcc/data/", include("apps.tcc_data.urls")),
    path("api/v1/tcc/intelligence/", include("apps.tcc_intelligence.urls")),
    path("api/v1/tcc/emulator/", include("apps.tcc_emulator.urls")),
    path("api/v1/tcc/reports/", include("apps.tcc_reports.urls")),
    path("api/v1/tcc/commerce/", include("apps.tcc_commerce.urls")),
    path("api/v1/tcc/alerts/", include("apps.tcc_alerts.urls")),
    # Workspace (template-based views)
    path("workspace/", include("apps.tcc_reports.workspace_urls")),
    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
