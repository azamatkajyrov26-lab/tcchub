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
    path("api/v1/landing/", include("apps.landing.urls")),
    path("site-admin/content/", include("apps.landing.admin_urls")),
    # TCC Analytics data backends
    path("api/v1/tcc/", include("apps.tcc_core.urls")),
    path("api/v1/tcc/data/", include("apps.tcc_data.urls")),
    path("api/v1/tcc/intelligence/", include("apps.tcc_intelligence.urls")),
    path("api/v1/tcc/reports/", include("apps.tcc_reports.urls")),
    path("api/v1/tcc/commerce/", include("apps.tcc_commerce.urls")),
    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
