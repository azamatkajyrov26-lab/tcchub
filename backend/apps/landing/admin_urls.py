from django.urls import path
from . import admin_views as v

app_name = "landing-admin"

urlpatterns = [
    path("", v.content_list, name="list"),
    path("new/", v.content_create, name="create"),
    path("<int:pk>/edit/", v.content_edit, name="edit"),
    path("<int:pk>/delete/", v.content_delete, name="delete"),
    path("<int:pk>/toggle/", v.content_toggle, name="toggle"),
    path("<int:pk>/move/<str:direction>/", v.content_move, name="move"),
]
