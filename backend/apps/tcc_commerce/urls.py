from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="products")
router.register("orders", views.OrderViewSet, basename="orders")
router.register("my-reports", views.MyReportAccessViewSet, basename="my-reports")

urlpatterns = [
    path("", include(router.urls)),
]
