from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CertificateTemplateViewSet, IssuedCertificateViewSet

router = DefaultRouter()
router.register("templates", CertificateTemplateViewSet, basename="certificate-template")
router.register("issued", IssuedCertificateViewSet, basename="issued-certificate")

urlpatterns = [
    path("", include(router.urls)),
]
