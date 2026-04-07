from rest_framework import viewsets
from rest_framework.permissions import AllowAny, SAFE_METHODS

from apps.accounts.permissions import IsAdmin

from .models import Advantage, ContactInfo, HeroSection, Metric, Partner, Testimonial
from .serializers import (
    AdvantageSerializer,
    ContactInfoSerializer,
    HeroSectionSerializer,
    MetricSerializer,
    PartnerSerializer,
    TestimonialSerializer,
)


class LandingPermission:
    """Read-only for everyone, write for admins."""

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdmin()]


class HeroSectionViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = HeroSection.objects.filter(is_active=True)
    serializer_class = HeroSectionSerializer


class MetricViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer


class PartnerViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


class TestimonialViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer


class AdvantageViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = Advantage.objects.all()
    serializer_class = AdvantageSerializer


class ContactInfoViewSet(LandingPermission, viewsets.ModelViewSet):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer
