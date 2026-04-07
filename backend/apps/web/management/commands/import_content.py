"""
Import video URLs, materials, and course covers into TCC HUB.

Usage:
    # Import from a JSON config file:
    python manage.py import_content --config /path/to/content.json

    # Generate placeholder covers for courses without images:
    python manage.py import_content --generate-covers

JSON config format:
{
    "courses": {
        "logistika-prodvinutyh-potok-3": {
            "cover_url": "https://example.com/cover.jpg",
            "modules": {
                "Модуль 1: Геополитика и BRI": {
                    "video_url": "https://www.youtube.com/watch?v=xxxxx",
                    "materials": [
                        {"title": "Презентация: ...", "url": "https://..."},
                        {"title": "Документ: ...", "file": "/path/to/file.pdf"}
                    ]
                }
            }
        }
    }
}
"""

import json
import os
import urllib.request
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.content.models import Activity, Resource
from apps.courses.models import Course, Section


class Command(BaseCommand):
    help = "Import video URLs, materials, and course covers"

    def add_arguments(self, parser):
        parser.add_argument("--config", type=str, help="Path to JSON config file")
        parser.add_argument(
            "--generate-covers",
            action="store_true",
            help="Generate SVG covers for courses without images",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        if options["generate_covers"]:
            self.generate_covers(options["dry_run"])

        if options["config"]:
            self.import_from_config(options["config"], options["dry_run"])

        if not options["config"] and not options["generate_covers"]:
            self.stdout.write(self.style.WARNING("Specify --config or --generate-covers"))
            self.show_current_state()

    def show_current_state(self):
        """Show current courses and their content status."""
        self.stdout.write("\n=== Current courses ===")
        for course in Course.objects.all():
            cover = "YES" if course.cover_image else "NO"
            self.stdout.write(f"\n  [{course.slug}] {course.title} (cover: {cover})")
            for section in Section.objects.filter(course=course, is_visible=True):
                activities = section.activities.filter(is_visible=True)
                video_act = activities.filter(
                    activity_type__in=["video", "folder", "lesson"]
                ).first()
                has_video = False
                if video_act:
                    try:
                        res = video_act.resource
                        has_video = bool(res.external_url or res.file)
                    except Resource.DoesNotExist:
                        pass
                video_status = "VIDEO" if has_video else "NO VIDEO"
                mat_count = activities.exclude(
                    activity_type__in=["video", "folder", "lesson", "quiz", "assignment"]
                ).count()
                self.stdout.write(
                    f"    {section.title} [{video_status}] [{mat_count} materials]"
                )

    def import_from_config(self, config_path, dry_run=False):
        """Import content from JSON config file."""
        with open(config_path) as f:
            config = json.load(f)

        courses_data = config.get("courses", {})
        for slug, course_data in courses_data.items():
            try:
                course = Course.objects.get(slug=slug)
            except Course.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Course not found: {slug}"))
                continue

            self.stdout.write(f"\nProcessing: {course.title}")

            # Cover image
            cover_url = course_data.get("cover_url")
            if cover_url and not course.cover_image:
                if dry_run:
                    self.stdout.write(f"  [DRY RUN] Would set cover from: {cover_url}")
                else:
                    self._download_cover(course, cover_url)

            # Modules
            modules = course_data.get("modules", {})
            for section_title, module_data in modules.items():
                section = Section.objects.filter(
                    course=course, title__icontains=section_title.split(":")[0]
                ).first()
                if not section:
                    section = Section.objects.filter(
                        course=course, title=section_title
                    ).first()
                if not section:
                    self.stdout.write(
                        self.style.WARNING(f"  Section not found: {section_title}")
                    )
                    continue

                # Video URL
                video_url = module_data.get("video_url")
                if video_url:
                    video_act = section.activities.filter(
                        activity_type__in=["video", "folder", "lesson"], is_visible=True
                    ).first()
                    if video_act:
                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Would set video URL for '{video_act.title}': {video_url}"
                            )
                        else:
                            resource, created = Resource.objects.get_or_create(
                                activity=video_act,
                                defaults={"external_url": video_url},
                            )
                            if not created and not resource.external_url:
                                resource.external_url = video_url
                                resource.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  Set video URL for '{video_act.title}'"
                                )
                            )

                # Materials
                materials = module_data.get("materials", [])
                for mat_data in materials:
                    mat_title = mat_data.get("title", "")
                    mat_url = mat_data.get("url", "")
                    mat_file = mat_data.get("file", "")

                    # Find matching material activity
                    mat_act = section.activities.filter(
                        title__icontains=mat_title.split(":")[0] if ":" in mat_title else mat_title,
                        is_visible=True,
                    ).exclude(activity_type__in=["video", "folder", "lesson", "quiz", "assignment"]).first()

                    if not mat_act:
                        # Find any resource/document activity
                        mat_act = section.activities.filter(
                            activity_type__in=["resource", "document"],
                            is_visible=True,
                        ).first()

                    if mat_act:
                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Would set material for '{mat_act.title}'"
                            )
                        else:
                            resource, _ = Resource.objects.get_or_create(activity=mat_act)
                            if mat_url:
                                resource.external_url = mat_url
                            if mat_file and os.path.exists(mat_file):
                                with open(mat_file, "rb") as fh:
                                    fname = os.path.basename(mat_file)
                                    resource.file.save(fname, ContentFile(fh.read()))
                                    resource.file_size = os.path.getsize(mat_file)
                                    ext = fname.rsplit(".", 1)[-1] if "." in fname else ""
                                    resource.file_type = ext
                            resource.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  Set material for '{mat_act.title}'"
                                )
                            )

        self.stdout.write(self.style.SUCCESS("\nImport complete!"))

    def _download_cover(self, course, url):
        """Download cover image from URL and save to course."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TCC-HUB/1.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            data = resp.read()
            ext = url.rsplit(".", 1)[-1].split("?")[0][:4]
            if ext not in ("jpg", "jpeg", "png", "webp"):
                ext = "jpg"
            fname = f"course_{course.slug}.{ext}"
            course.cover_image.save(fname, ContentFile(data))
            self.stdout.write(self.style.SUCCESS(f"  Cover saved: {fname}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Cover download failed: {e}"))

    def generate_covers(self, dry_run=False):
        """Generate SVG-based cover images for courses without covers."""
        colors = [
            ("#1B2A4A", "#C6A46D"),
            ("#0F3460", "#E94560"),
            ("#2C3333", "#A5C9CA"),
            ("#1A1A2E", "#E94560"),
            ("#16213E", "#0F3460"),
            ("#1B262C", "#3282B8"),
            ("#2D4059", "#FF6B6B"),
            ("#222831", "#00ADB5"),
        ]

        courses = Course.objects.all()
        for i, course in enumerate(courses):
            if course.cover_image:
                self.stdout.write(f"  [{course.slug}] Already has cover, skipping")
                continue

            bg, accent = colors[i % len(colors)]

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would generate cover for: {course.title}"
                )
                continue

            # Generate SVG cover
            title_lines = self._wrap_text(course.title, 25)
            title_svg = ""
            y_start = 140 - (len(title_lines) - 1) * 18
            for idx, line in enumerate(title_lines):
                escaped = line.replace("&", "&amp;").replace("<", "&lt;")
                title_svg += f'<text x="40" y="{y_start + idx * 36}" fill="white" font-family="sans-serif" font-size="28" font-weight="bold">{escaped}</text>\n'

            svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{accent}22"/>
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <rect x="0" y="420" width="800" height="30" fill="{accent}" opacity="0.8"/>
  <circle cx="700" cy="100" r="180" fill="{accent}" opacity="0.06"/>
  <circle cx="650" cy="350" r="120" fill="{accent}" opacity="0.04"/>
  {title_svg}
  <text x="40" y="{y_start + len(title_lines) * 36 + 10}" fill="{accent}" font-family="sans-serif" font-size="14" font-weight="600">TCC HUB · Платформа обучения</text>
  <rect x="40" y="400" width="60" height="4" rx="2" fill="{accent}" opacity="0.6"/>
</svg>"""

            # Convert SVG to a file
            fname = f"cover_{course.slug}.svg"
            course.cover_image.save(fname, ContentFile(svg.encode("utf-8")))
            self.stdout.write(self.style.SUCCESS(f"  Generated cover for: {course.title}"))

        self.stdout.write(self.style.SUCCESS("\nCovers generated!"))

    def _wrap_text(self, text, max_chars):
        """Wrap text into lines of max_chars."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if current and len(current) + len(word) + 1 > max_chars:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}" if current else word
        if current:
            lines.append(current)
        return lines
