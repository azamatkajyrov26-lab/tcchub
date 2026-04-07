"""
Match scraped Moodle data to TCC HUB courses and import video URLs + file links.
"""
import json
import os
import re
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from apps.content.models import Activity, Resource
from apps.courses.models import Course, Section


# Mapping: Moodle course ID -> TCC HUB course slug
# Based on matching titles:
#   Moodle "Логистика с нуля 1 поток" -> HUB "logistika-s-nulya-potok-1"
COURSE_MAP = {
    2: "logistika-s-nulya-potok-1",     # Авторский курс "Логистика с нуля" 1 поток
    3: "logistika-s-nulya-potok-2",     # Авторский курс "Логистика с нуля" 2 поток
    4: "logistika-s-nulya-potok-3",     # Авторский курс "Логистика с нуля" 3 поток
    8: "logistika-s-nulya-potok-4",     # Авторский курс "Логистика с нуля" 4 поток
    10: "logistika-navigaciya-potok-5", # «Логистика с нуля. Навигация входа в профессию» 5 поток
    5: "logistika-prodvinutyh-potok-1", # Авторский курс "Логистика для продвинутых" 1 поток
    7: "logistika-prodvinutyh-potok-2", # Авторский курс "Логистика для продвинутых" 2 поток
    9: "logistika-prodvinutyh-potok-3", # "Логистика для продвинутых" 3 поток
}


def normalize(text):
    """Normalize section title for matching."""
    text = text.lower().strip()
    text = re.sub(r'\s*\(\d+\s*час[а-я]*\)', '', text)  # remove (4 часа)
    text = re.sub(r'^модуль\s*\d+[.:]\s*', '', text)     # remove "Модуль N: "
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def match_section(moodle_title, hub_sections):
    """Find best matching HUB section for a Moodle section title."""
    norm_moodle = normalize(moodle_title)

    best_match = None
    best_score = 0

    for section in hub_sections:
        norm_hub = normalize(section.title)

        # Exact match after normalization
        if norm_moodle == norm_hub:
            return section

        # Check keyword overlap
        moodle_words = set(norm_moodle.split())
        hub_words = set(norm_hub.split())
        common = moodle_words & hub_words
        if len(common) > best_score and len(common) >= 2:
            best_score = len(common)
            best_match = section

    return best_match


def main():
    with open("/app/moodle_content.json") as f:
        moodle_data = json.load(f)

    total_videos = 0
    total_files = 0
    skipped = 0

    for moodle_course in moodle_data:
        moodle_id = moodle_course["id"]
        hub_slug = COURSE_MAP.get(moodle_id)
        if not hub_slug:
            print(f"\nSKIP: No mapping for Moodle course {moodle_id}: {moodle_course['title']}")
            continue

        try:
            hub_course = Course.objects.get(slug=hub_slug)
        except Course.DoesNotExist:
            print(f"\nERROR: HUB course not found: {hub_slug}")
            continue

        hub_sections = list(Section.objects.filter(course=hub_course, is_visible=True))
        print(f"\n{'='*60}")
        print(f"Moodle: {moodle_course['title']} (id={moodle_id})")
        print(f"HUB:    {hub_course.title} ({hub_slug})")
        print(f"{'='*60}")

        for moodle_sec in moodle_course["sections"]:
            hub_section = match_section(moodle_sec["title"], hub_sections)

            if not hub_section:
                # Try matching by section number
                sec_num = moodle_sec.get("num", "")
                for hs in hub_sections:
                    if f"Модуль {sec_num}" in hs.title:
                        hub_section = hs
                        break

            if not hub_section:
                print(f"  SKIP section: {moodle_sec['title']} (no match)")
                skipped += 1
                continue

            print(f"\n  Moodle: {moodle_sec['title']}")
            print(f"  HUB:    {hub_section.title}")

            # Find the primary video activity in this HUB section (folder/video/lesson)
            video_act = hub_section.activities.filter(
                activity_type__in=["video", "folder", "lesson"],
                is_visible=True,
            ).first()

            # Get video URL from Moodle activities
            video_url = None
            file_urls = []
            for act in moodle_sec["activities"]:
                if act["video_url"] and not video_url:
                    video_url = act["video_url"]
                for f in act["files"]:
                    file_urls.append(f)

            # Import video URL
            if video_url and video_act:
                resource, created = Resource.objects.get_or_create(
                    activity=video_act,
                    defaults={"external_url": video_url},
                )
                if not created:
                    if not resource.external_url:
                        resource.external_url = video_url
                        resource.save()
                print(f"    VIDEO: {video_url} -> {video_act.title}")
                total_videos += 1
            elif video_url and not video_act:
                print(f"    VIDEO: {video_url} (no video activity in HUB section)")

            # Import file URLs to the resource/document activity
            if file_urls:
                mat_act = hub_section.activities.filter(
                    activity_type__in=["resource", "document"],
                    is_visible=True,
                ).first()
                if mat_act:
                    resource, _ = Resource.objects.get_or_create(activity=mat_act)
                    # Store first file URL as external_url
                    if not resource.external_url and file_urls:
                        resource.external_url = file_urls[0]["url"][:1024]
                        resource.save()
                    print(f"    FILES: {len(file_urls)} files -> {mat_act.title}")
                    total_files += len(file_urls)
                else:
                    print(f"    FILES: {len(file_urls)} files (no material activity)")

    print(f"\n\n{'='*60}")
    print(f"DONE: {total_videos} videos imported, {total_files} file links added, {skipped} sections skipped")


if __name__ == "__main__":
    main()
