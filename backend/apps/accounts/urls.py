from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, RegisterView, UserViewSet

app_name = "accounts_api"

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    # Auth endpoints — match frontend expectations
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", UserViewSet.as_view({"get": "me", "patch": "me"}), name="me"),
    # User CRUD
    path("", include(router.urls)),
]
