"""Add CASPIA Lab (caspia-lab.az) as an international partner per client request.

Run on production:
    python manage.py add_partner_caspia_2026_07_15
"""
from django.core.management.base import BaseCommand
from django.db.models import Max

from apps.landing.models import SiteItem


class Command(BaseCommand):
    help = "Add CASPIA Lab as an international partner (2026-07-15 client request)"

    def handle(self, *args, **options):
        qs = SiteItem.objects.filter(category="partner", subcategory="international")
        next_order = (qs.aggregate(Max("order"))["order__max"] or 0) + 1

        obj, created = SiteItem.objects.get_or_create(
            category="partner",
            subcategory="international",
            title="CASPIA",
            defaults={
                "description": "Аналитический центр геополитических исследований Каспийского региона и Центральной Азии",
                "image_url": "/static/img/partners/caspia_lab.png",
                "link_url": "https://caspia-lab.az/",
                "order": next_order,
                "is_published": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"[partner] created #{obj.pk} 'CASPIA' (order={next_order})"))
        else:
            self.stdout.write(self.style.WARNING("[partner] 'CASPIA' already exists, skipped"))
