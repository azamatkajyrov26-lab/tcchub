from django.core.management.base import BaseCommand

from apps.tcc_commerce.models import Product
from apps.tcc_reports.models import Report


class Command(BaseCommand):
    help = "Создаёт продукты для опубликованных отчётов"

    def handle(self, *args, **options):
        created = 0

        # Create products for published reports that don't have one yet
        for report in Report.objects.filter(status="published"):
            product, is_new = Product.objects.get_or_create(
                report=report,
                product_type="single_report",
                defaults={
                    "name": report.title,
                    "description": f"Полный доступ к отчёту: {report.title}",
                    "price_usd": report.price_usd,
                    "is_active": True,
                },
            )
            if is_new:
                created += 1
                self.stdout.write(f"  + {product.name} (${product.price_usd})")

        # Subscription products
        subs = [
            {
                "product_type": "subscription_monthly",
                "name": "Месячная подписка TCC Analytics",
                "description": "Доступ ко всем отчётам на 1 месяц",
                "price_usd": 99,
            },
            {
                "product_type": "subscription_annual",
                "name": "Годовая подписка TCC Analytics",
                "description": "Доступ ко всем отчётам на 12 месяцев. Экономия 40%.",
                "price_usd": 699,
            },
        ]
        for sub in subs:
            product, is_new = Product.objects.get_or_create(
                product_type=sub["product_type"],
                name=sub["name"],
                defaults={
                    "description": sub["description"],
                    "price_usd": sub["price_usd"],
                    "is_active": True,
                },
            )
            if is_new:
                created += 1
                self.stdout.write(f"  + {product.name} (${product.price_usd})")

        self.stdout.write(self.style.SUCCESS(f"Продукты: создано {created}"))
