from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdvantageViewSet,
    ContactInfoViewSet,
    HeroSectionViewSet,
    MetricViewSet,
    PartnerViewSet,
    TestimonialViewSet,
)

router = DefaultRouter()
router.register("hero", HeroSectionViewSet, basename="hero-section")
router.register("metrics", MetricViewSet, basename="metric")
router.register("partners", PartnerViewSet, basename="partner")
router.register("testimonials", TestimonialViewSet, basename="testimonial")
router.register("advantages", AdvantageViewSet, basename="advantage")
router.register("contact", ContactInfoViewSet, basename="contact-info")

urlpatterns = [
    path("", include(router.urls)),
]
