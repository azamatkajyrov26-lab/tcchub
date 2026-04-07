from rest_framework import serializers

from .models import Advantage, ContactInfo, HeroSection, Metric, Partner, Testimonial


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ["id", "title", "subtitle", "background_image", "cta_text", "cta_url", "is_active"]
        read_only_fields = ["id"]


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ["id", "label", "value", "description", "order"]
        read_only_fields = ["id"]


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ["id", "name", "logo", "url", "order"]
        read_only_fields = ["id"]


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ["id", "author_name", "author_role", "content", "avatar", "order"]
        read_only_fields = ["id"]


class AdvantageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advantage
        fields = ["id", "title", "description", "icon", "order"]
        read_only_fields = ["id"]


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ["id", "address", "phone", "email", "whatsapp", "linkedin", "instagram"]
        read_only_fields = ["id"]
