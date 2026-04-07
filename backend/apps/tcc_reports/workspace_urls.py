"""
URL configuration for workspace (template-based views with HTMX).
"""

from django.urls import path

from apps.tcc_reports import workspace_views as views

urlpatterns = [
    # Workspace pages
    path("reports/", views.workspace_reports_list, name="workspace-reports"),
    path("reports/new/", views.workspace_report_create, name="workspace-report-create"),
    path("reports/<int:pk>/edit/", views.workspace_report_edit, name="workspace-report-edit"),
    # HTMX endpoints
    path("reports/<int:pk>/save-meta/", views.save_report_meta, name="save-report-meta"),
    path("sections/<int:pk>/save/", views.save_section, name="save-section"),
    path("reports/<int:report_pk>/add-section/", views.add_section, name="add-section"),
    # HTMX partials
    path("htmx/corridor-scores/", views.htmx_corridor_scores, name="htmx-corridor-scores"),
    path("htmx/risk-factors/", views.htmx_risk_factors, name="htmx-risk-factors"),
    path("htmx/recent-alerts/", views.htmx_recent_alerts, name="htmx-recent-alerts"),
    path("htmx/recent-news/", views.htmx_recent_news, name="htmx-recent-news"),
    path("htmx/sanction-check/", views.htmx_sanction_check, name="htmx-sanction-check"),
    path("htmx/scenarios/", views.htmx_scenarios, name="htmx-scenarios"),
]
