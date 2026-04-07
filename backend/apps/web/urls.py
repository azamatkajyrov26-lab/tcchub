from django.urls import path, re_path
from django.http import HttpResponse
from django.views.generic import TemplateView

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
    # Main site pages
    path("", views.landing_view, name="landing"),
    path("about/", views.about_view, name="about"),
    path("analytics/", views.site_analytics_view, name="site_analytics"),
    path("solutions/", views.solutions_view, name="solutions"),
    path("education/", views.education_view, name="education"),
    path("projects/", views.projects_view, name="projects"),
    path("press/", views.site_media_view, name="site_media"),
    path("partners/", views.site_partners_view, name="site_partners"),
    path("contacts/", views.contacts_view, name="contacts"),
    path("wiki/", views.wiki_view, name="wiki"),
    path("corridor/", views.corridor_view, name="corridor"),
    path("live-data/", views.live_data_view, name="live_data"),
    path("corridor-map/", views.corridor_map_view, name="corridor_map"),
    path("monitoring/", views.monitoring_view, name="monitoring"),

    # Data exports (CSV)
    path("export/route-scores/", views.export_route_scores_view, name="export_route_scores"),
    path("export/risk-factors/", views.export_risk_factors_view, name="export_risk_factors"),
    path("export/trade-flows/", views.export_trade_flows_view, name="export_trade_flows"),
    path("export/sanctions/", views.export_sanctions_view, name="export_sanctions"),
    path("kz-logistics-laws/", views.kz_logistics_laws_view, name="kz_logistics_laws"),
    path("analytics/<slug:slug>/", views.article_detail_view, name="article_detail"),

    # Reports catalog & commerce
    path("reports/", views.reports_catalog_view, name="reports_catalog"),
    re_path(r"^reports/(?P<slug>[^/]+)/$", views.report_detail_view, name="report_detail"),
    re_path(r"^reports/(?P<slug>[^/]+)/buy/$", views.buy_report_view, name="buy_report"),

    # Client dashboard — reports & orders
    path("dashboard/my-reports/", views.dashboard_my_reports_view, name="dashboard_my_reports"),
    path("dashboard/my-orders/", views.dashboard_my_orders_view, name="dashboard_my_orders"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Courses
    path("courses/", views.courses_view, name="courses"),
    path("courses/<slug:slug>/", views.course_detail_view, name="course_detail"),
    path("courses/<slug:slug>/enroll/", views.enroll_view, name="enroll"),
    path("courses/<slug:slug>/activity/<int:activity_id>/", views.activity_detail_view, name="activity_detail"),
    path("courses/<slug:slug>/activity/<int:activity_id>/complete/", views.complete_activity_view, name="complete_activity"),
    path("courses/<slug:slug>/activity/<int:activity_id>/video-progress/", views.save_video_progress_view, name="save_video_progress"),

    # Quizzes
    path("quiz/<int:quiz_id>/", views.quiz_start_view, name="quiz_start"),
    path("quiz/<int:quiz_id>/take/<int:attempt_id>/", views.quiz_take_view, name="quiz_take"),
    path("quiz/<int:quiz_id>/take/<int:attempt_id>/submit/", views.quiz_submit_view, name="quiz_submit"),
    path("quiz/<int:quiz_id>/results/<int:attempt_id>/", views.quiz_results_view, name="quiz_results"),

    # Assignments
    path("assignment/<int:assignment_id>/", views.assignment_detail_view, name="assignment_detail"),
    path("assignment/<int:assignment_id>/submit/", views.assignment_submit_view, name="assignment_submit"),

    # Grades
    path("grades/", views.grades_view, name="grades"),

    # Certificates
    path("certificates/", views.certificates_view, name="certificates"),

    # Messages
    path("messages/", views.messages_view, name="messages"),
    path("messages/<int:conversation_id>/", views.conversation_view, name="conversation"),
    path("messages/<int:conversation_id>/send/", views.send_message_view, name="send_message"),

    # Notifications
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),

    # Calendar
    path("calendar/", views.calendar_view, name="calendar"),

    # Profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.change_password_view, name="change_password"),
]
