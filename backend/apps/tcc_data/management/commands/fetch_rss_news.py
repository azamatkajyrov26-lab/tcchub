"""
Management command: python manage.py fetch_rss_news

Fetches news from all configured RSS sources about the Middle Corridor.
Run manually or schedule via Celery Beat every 6 hours.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fetch logistics news from RSS feeds (Middle Corridor, TMTM, BRI)"

    def handle(self, *args, **options):
        from apps.tcc_data.fetchers.rss_feeds import fetch_all_rss_feeds

        self.stdout.write("Fetching RSS news from all sources...")
        result = fetch_all_rss_feeds()

        self.stdout.write(f"\nSources processed: {result['sources']}")
        self.stdout.write(f"Total new articles: {result['total_new']}")

        for detail in result.get("details", []):
            status = "OK" if detail["fetched"] > 0 else "EMPTY"
            self.stdout.write(
                f"  [{status}] {detail['source']}: "
                f"{detail['fetched']} fetched, {detail['new']} new"
            )

        self.stdout.write(self.style.SUCCESS("\nDone!"))
