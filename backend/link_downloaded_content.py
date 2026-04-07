"""
Properly link downloaded videos and materials to Django Resource objects.
Scans /app/media/courses/<slug>/ directories and matches files to activities
using the module prefix (module_NN) and section matching.
"""
import os
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.core.files import File

from apps.content.models import Activity, Resource, Folder, FolderFile
from apps.courses.models import Course, Section

MEDIA_ROOT = Path("/app/media")
COURSES_DIR = MEDIA_ROOT / "courses"

VIDEO_TYPES = {"video", "folder", "lesson"}
MATERIAL_TYPES = {"resource", "document"}


def main():
    stats = {"videos_linked": 0, "materials_linked": 0, "errors": 0}

    for course_dir in sorted(COURSES_DIR.iterdir()):
        if not course_dir.is_dir() or course_dir.name in ("covers",):
            continue

        slug = course_dir.name
        try:
            course = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            print(f"SKIP: No course for slug '{slug}'")
            continue

        print(f"\n{'='*60}")
        print(f"COURSE: {course.title} ({slug})")
        print(f"{'='*60}")

        sections = list(
            Section.objects.filter(course=course, is_visible=True).order_by("order")
        )

        videos_dir = course_dir / "videos"
        materials_dir = course_dir / "materials"

        # --- Link videos ---
        if videos_dir.exists():
            video_files = sorted(videos_dir.glob("*.mp4"))
            print(f"  Found {len(video_files)} video files")

            # Group video files by module prefix
            module_videos = {}
            for vf in video_files:
                m = re.match(r"module_(\d+)", vf.name)
                if m:
                    mod_num = int(m.group(1))
                    # Keep the latest one per module (in case of duplicates)
                    module_videos[mod_num] = vf

            for sec_idx, section in enumerate(sections, 1):
                video_act = section.activities.filter(
                    activity_type__in=VIDEO_TYPES, is_visible=True
                ).first()
                if not video_act:
                    continue

                # Try to find video file for this section
                video_file = module_videos.get(sec_idx)

                if not video_file:
                    # Try matching by section title in filename
                    for vf in video_files:
                        # Normalize both for comparison
                        vf_lower = vf.stem.lower().replace("_", " ")
                        sec_lower = section.title.lower()
                        # Check keyword overlap
                        sec_words = set(re.findall(r'\w+', sec_lower))
                        vf_words = set(re.findall(r'\w+', vf_lower))
                        if len(sec_words & vf_words) >= 2:
                            video_file = vf
                            break

                if not video_file:
                    print(f"  [{sec_idx}] {section.title} — NO VIDEO FILE")
                    continue

                # Save via Django File API
                resource, _ = Resource.objects.get_or_create(activity=video_act)
                relative_path = str(video_file.relative_to(MEDIA_ROOT))

                # Check if already correctly linked
                if resource.file and resource.file.name == relative_path:
                    actual_path = MEDIA_ROOT / resource.file.name
                    if actual_path.exists():
                        print(f"  [{sec_idx}] {video_act.title} — OK (already linked)")
                        stats["videos_linked"] += 1
                        continue

                # Set file.name directly (file already in media dir, no need to copy)
                resource.file.name = relative_path
                resource.file_type = "video/mp4"
                resource.file_size = video_file.stat().st_size
                resource.save()
                size_mb = video_file.stat().st_size / 1024 / 1024
                print(f"  [{sec_idx}] {video_act.title} — LINKED ({size_mb:.0f} MB)")
                stats["videos_linked"] += 1

        # --- Link materials ---
        if materials_dir.exists():
            mat_files = sorted(materials_dir.glob("*"))
            mat_files = [f for f in mat_files if f.is_file()]
            print(f"  Found {len(mat_files)} material files")

            # Group by module prefix
            module_materials = {}
            for mf in mat_files:
                m = re.match(r"module_(\d+)_", mf.name)
                if m:
                    mod_num = int(m.group(1))
                    module_materials.setdefault(mod_num, []).append(mf)

            for sec_idx, section in enumerate(sections, 1):
                files_for_section = module_materials.get(sec_idx, [])
                if not files_for_section:
                    continue

                # Find material activity
                mat_act = section.activities.filter(
                    activity_type__in=MATERIAL_TYPES, is_visible=True
                ).first()

                if not mat_act:
                    # Try any non-video activity
                    mat_act = section.activities.filter(
                        is_visible=True
                    ).exclude(
                        activity_type__in=VIDEO_TYPES
                    ).exclude(
                        activity_type__in=["quiz", "assignment"]
                    ).first()

                if not mat_act:
                    print(f"  [{sec_idx}] {section.title} — {len(files_for_section)} files but NO MATERIAL ACTIVITY")
                    continue

                # Link first file to Resource
                first_file = files_for_section[0]
                resource, _ = Resource.objects.get_or_create(activity=mat_act)
                relative_path = str(first_file.relative_to(MEDIA_ROOT))

                resource.file.name = relative_path
                ext = first_file.suffix.lstrip(".")
                resource.file_type = ext
                resource.file_size = first_file.stat().st_size
                resource.save()

                print(f"  [{sec_idx}] {mat_act.title} — LINKED {len(files_for_section)} files")
                stats["materials_linked"] += len(files_for_section)

                # If activity is a folder type and has Folder model, add files there
                if mat_act.activity_type == "folder":
                    folder, _ = Folder.objects.get_or_create(
                        activity=mat_act,
                        defaults={"name": mat_act.title}
                    )
                    for mf in files_for_section:
                        rel = str(mf.relative_to(MEDIA_ROOT))
                        ff, created = FolderFile.objects.get_or_create(
                            folder=folder,
                            original_name=mf.name,
                            defaults={"file": rel}
                        )
                        if not created and ff.file.name != rel:
                            ff.file.name = rel
                            ff.save()

    # --- Verification ---
    print(f"\n\n{'='*60}")
    print("VERIFICATION")
    print(f"{'='*60}")

    total_video_res = Resource.objects.filter(
        activity__activity_type__in=VIDEO_TYPES
    )
    ok = 0
    broken = 0
    for r in total_video_res:
        if r.file and r.file.name:
            full_path = MEDIA_ROOT / r.file.name
            if full_path.exists() and full_path.stat().st_size > 1000:
                ok += 1
            else:
                broken += 1
                print(f"  BROKEN: {r.activity.title} -> {r.file.name}")
        elif r.external_url:
            ok += 1  # Has YouTube fallback
        else:
            broken += 1
            print(f"  EMPTY: {r.activity.title}")

    print(f"\nVideo resources: {ok} OK, {broken} broken")
    print(f"Videos linked: {stats['videos_linked']}")
    print(f"Materials linked: {stats['materials_linked']}")

    # Show per-course summary
    print(f"\n{'='*60}")
    print("PER-COURSE SUMMARY")
    print(f"{'='*60}")
    for course in Course.objects.all().order_by("slug"):
        sections = Section.objects.filter(course=course, is_visible=True)
        total_acts = 0
        with_video = 0
        with_material = 0
        for sec in sections:
            for act in sec.activities.filter(is_visible=True):
                total_acts += 1
                try:
                    res = act.resource
                    if act.activity_type in VIDEO_TYPES:
                        if (res.file and res.file.name) or res.external_url:
                            with_video += 1
                    elif act.activity_type in MATERIAL_TYPES:
                        if (res.file and res.file.name) or res.external_url:
                            with_material += 1
                except Resource.DoesNotExist:
                    pass
        print(f"  {course.slug}: {with_video} videos, {with_material} materials / {total_acts} activities")


if __name__ == "__main__":
    main()
