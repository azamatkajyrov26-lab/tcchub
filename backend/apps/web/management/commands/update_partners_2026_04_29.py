"""Update partners (ISCO, Intertek descriptions; EUCA/APEC Industries/INTERTEK logos)
and Nargiza Turarbek expert description per client request.

Run on production:
    python manage.py update_partners_2026_04_29
"""
from django.core.management.base import BaseCommand
from apps.landing.models import SiteItem


PARTNER_UPDATES = [
    # (title_contains, fields_to_update)
    ("ISCO", {"description": "Международный оператор цепочки поставок"}),
    ("Intertek", {"description": "Аренда и продажа спецтехники в Казахстане"}),
    ("EUCA", {"image_url": "/static/img/partners/euca_new.png", "image": ""}),
    ("APEC Industries", {"image_url": "/static/img/partners/apec_industries_new.png", "image": ""}),
    ("INTERTEK", {"image_url": "/static/img/partners/intertek_new.png", "image": ""}),
]

EXPERT_UPDATES = [
    ("Наргиза", {"description": "Эксперт в сфере рекрутинга и HR. Опыт более 7 лет"}),
]


class Command(BaseCommand):
    help = "Apply partner + expert content updates from 2026-04-29 client request"

    def handle(self, *args, **options):
        for needle, fields in PARTNER_UPDATES:
            qs = SiteItem.objects.filter(category="partner", title__icontains=needle)
            count = qs.count()
            if not count:
                self.stdout.write(self.style.WARNING(f"[partner] no match for '{needle}'"))
                continue
            for item in qs:
                for k, v in fields.items():
                    setattr(item, k, v)
                item.save(update_fields=list(fields.keys()) + ["updated_at"])
                self.stdout.write(self.style.SUCCESS(f"[partner] updated #{item.pk} '{item.title}' -> {fields}"))

        for needle, fields in EXPERT_UPDATES:
            qs = SiteItem.objects.filter(category="expert", title__icontains=needle)
            count = qs.count()
            if not count:
                self.stdout.write(self.style.WARNING(f"[expert] no match for '{needle}'"))
                continue
            for item in qs:
                for k, v in fields.items():
                    setattr(item, k, v)
                item.save(update_fields=list(fields.keys()) + ["updated_at"])
                self.stdout.write(self.style.SUCCESS(f"[expert] updated #{item.pk} '{item.title}' -> {fields}"))

        self.stdout.write(self.style.SUCCESS("Done."))
