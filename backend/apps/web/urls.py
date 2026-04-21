from django.urls import path, re_path
from django.http import HttpResponse

from . import views


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /accounts/\n"
        "Disallow: /api/\n"
        "Disallow: /export/\n\n"
        "Sitemap: https://tc-cargo.kz/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    pages = [
        "", "about/", "analytics/", "solutions/", "education/",
        "projects/", "press/", "partners/", "contacts/",
        "wiki/", "corridor/", "live-data/", "corridor-map/",
        "monitoring/", "kz-logistics-laws/", "reports/",
    ]
    urls = "".join(
        f"<url><loc>https://tc-cargo.kz/{p}</loc><changefreq>weekly</changefreq><priority>{'1.0' if not p else '0.8'}</priority></url>"
        for p in pages
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(xml, content_type="application/xml")


urlpatterns = [
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),

    # Public pages
    path("", views.landing_view, name="landing"),
    path("about/", views.about_view, name="about"),
    path("analytics/", views.site_analytics_view, name="site_analytics"),
    path("solutions/", views.solutions_view, name="solutions"),
    path("education/", views.education_view, name="education"),
    path("projects/", views.projects_view, name="projects"),
    path("press/", views.site_media_view, name="site_media"),
    path("partners/", views.site_partners_view, name="site_partners"),
    path("contacts/", views.contacts_view, name="contacts"),
    path("contacts/submit/", views.contact_submit_view, name="contact_submit"),
    path("tg/webhook/", views.telegram_webhook_view, name="telegram_webhook"),
    path("wiki/", views.wiki_view, name="wiki"),
    path("kz-logistics-laws/", views.kz_logistics_laws_view, name="kz_logistics_laws"),
    path("analytics/<slug:slug>/", views.article_detail_view, name="article_detail"),

    # Tools (gated by login)
    path("corridor/", views.corridor_view, name="corridor"),
    path("corridor-map/", views.corridor_map_view, name="corridor_map"),
    path("live-data/", views.live_data_view, name="live_data"),
    path("monitoring/", views.monitoring_view, name="monitoring"),

    # Data exports (login required)
    path("export/route-scores/", views.export_route_scores_view, name="export_route_scores"),
    path("export/risk-factors/", views.export_risk_factors_view, name="export_risk_factors"),
    path("export/trade-flows/", views.export_trade_flows_view, name="export_trade_flows"),
    path("export/sanctions/", views.export_sanctions_view, name="export_sanctions"),

    # Reports catalog & commerce
    path("reports/", views.reports_catalog_view, name="reports_catalog"),
    re_path(r"^reports/(?P<slug>[^/]+)/$", views.report_detail_view, name="report_detail"),
    re_path(r"^reports/(?P<slug>[^/]+)/buy/$", views.buy_report_view, name="buy_report"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Client cabinet
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/my-reports/", views.dashboard_my_reports_view, name="dashboard_my_reports"),
    path("dashboard/my-orders/", views.dashboard_my_orders_view, name="dashboard_my_orders"),
    path("dashboard/submissions/", views.dashboard_submissions_list, name="dashboard_submissions"),
    path("dashboard/cms/help/", views.dashboard_cms_help, name="dashboard_cms_help"),
    path("dashboard/cms/request/", views.dashboard_cms_request, name="dashboard_cms_request"),
    path("dashboard/cms/news/", views.dashboard_cms_news_list, name="dashboard_cms_news_list"),
    path("dashboard/cms/news/new/", views.dashboard_cms_news_edit, name="dashboard_cms_news_new"),
    path("dashboard/cms/news/<int:news_id>/", views.dashboard_cms_news_edit, name="dashboard_cms_news_edit"),
    path("dashboard/cms/news/<int:news_id>/delete/", views.dashboard_cms_news_delete, name="dashboard_cms_news_delete"),
    path("dashboard/cms/items/<str:category>/", views.dashboard_cms_items_list, name="dashboard_cms_items_list"),
    path("dashboard/cms/items/<str:category>/new/", views.dashboard_cms_items_edit, name="dashboard_cms_items_new"),
    path("dashboard/cms/items/<str:category>/<int:item_id>/", views.dashboard_cms_items_edit, name="dashboard_cms_items_edit"),
    path("dashboard/cms/items/<str:category>/<int:item_id>/delete/", views.dashboard_cms_items_delete, name="dashboard_cms_items_delete"),
    path("dashboard/cms/", views.dashboard_cms_list, name="dashboard_cms_list"),
    path("dashboard/cms/<slug:slug>/", views.dashboard_cms_page, name="dashboard_cms_page"),
    path("dashboard/cms/toggle/<int:section_id>/", views.dashboard_cms_toggle, name="dashboard_cms_toggle"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.change_password_view, name="change_password"),
]
