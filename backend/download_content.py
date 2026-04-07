"""
Download all videos (YouTube) and materials (Moodle files) and organize
them by course/section, then update the Django DB to point to local files.

Directory structure:
    /app/media/courses/<course_slug>/
        videos/
            module_01_<sanitized_title>.mp4
        materials/
            module_01_<original_filename>
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import requests
from django.core.files.base import ContentFile

from apps.content.models import Activity, Resource
from apps.courses.models import Course, Section

# Moodle course ID -> HUB course slug
COURSE_MAP = {
    2: "logistika-s-nulya-potok-1",
    3: "logistika-s-nulya-potok-2",
    4: "logistika-s-nulya-potok-3",
    8: "logistika-s-nulya-potok-4",
    10: "logistika-navigaciya-potok-5",
    5: "logistika-prodvinutyh-potok-1",
    7: "logistika-prodvinutyh-potok-2",
    9: "logistika-prodvinutyh-potok-3",
}

MOODLE_BASE = "https://tcchub.kz"
MOODLE_USER = "dana_kadyrgaliyeva"
MOODLE_PASS = "weg-z8P-WcB-mUY"

MEDIA_ROOT = Path("/app/media/courses")


def sanitize(name, max_len=80):
    """Make a filesystem-safe name."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:max_len]


def get_moodle_session():
    """Login to Moodle and return an authenticated requests.Session."""
    from bs4 import BeautifulSoup

    s = requests.Session()
    login_page = s.get(f"{MOODLE_BASE}/login/index.php")
    soup = BeautifulSoup(login_page.text, "html.parser")
    token = soup.find("input", {"name": "logintoken"})
    token_val = token["value"] if token else ""
    resp = s.post(
        f"{MOODLE_BASE}/login/index.php",
        data={
            "username": MOODLE_USER,
            "password": MOODLE_PASS,
            "logintoken": token_val,
        },
        allow_redirects=True,
    )
    if "login" in resp.url.lower() and "index.php" in resp.url:
        print("ERROR: Moodle login failed!", file=sys.stderr)
        sys.exit(1)
    print("Moodle login OK")
    return s


def download_youtube(url, output_path):
    """Download YouTube video using yt-dlp. Returns True on success."""
    if output_path.exists() and output_path.stat().st_size > 100_000:
        print(f"    SKIP (already exists): {output_path.name}")
        return True

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", str(output_path),
                "--no-playlist",
                "--socket-timeout", "30",
                "--retries", "3",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"    OK ({size_mb:.1f} MB): {output_path.name}")
            return True
        else:
            print(f"    FAIL: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT: {url}")
        return False
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def download_moodle_file(session, url, output_path):
    """Download file from Moodle using authenticated session."""
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"    SKIP (already exists): {output_path.name}")
        return True

    try:
        resp = session.get(url, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            size_kb = output_path.stat().st_size / 1024
            print(f"    OK ({size_kb:.1f} KB): {output_path.name}")
            return True
        else:
            print(f"    FAIL HTTP {resp.status_code}: {url[:80]}")
            return False
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def normalize(text):
    """Normalize section title for matching."""
    text = text.lower().strip()
    text = re.sub(r'\s*\(\d+\s*час[а-я]*\)', '', text)
    text = re.sub(r'^модуль\s*\d+[.:]\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def match_section(moodle_title, hub_sections):
    """Find best matching HUB section."""
    norm_moodle = normalize(moodle_title)
    best_match = None
    best_score = 0

    for section in hub_sections:
        norm_hub = normalize(section.title)
        if norm_moodle == norm_hub:
            return section
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

    moodle_session = get_moodle_session()

    stats = {"videos_ok": 0, "videos_fail": 0, "files_ok": 0, "files_fail": 0}

    for moodle_course in moodle_data:
        moodle_id = moodle_course["id"]
        slug = COURSE_MAP.get(moodle_id)
        if not slug:
            continue

        try:
            hub_course = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            print(f"\nERROR: Course not found: {slug}")
            continue

        hub_sections = list(Section.objects.filter(course=hub_course, is_visible=True))

        # Create directories
        course_dir = MEDIA_ROOT / slug
        videos_dir = course_dir / "videos"
        materials_dir = course_dir / "materials"
        videos_dir.mkdir(parents=True, exist_ok=True)
        materials_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"COURSE: {hub_course.title}")
        print(f"  slug: {slug}")
        print(f"  dir:  {course_dir}")
        print(f"{'='*60}")

        for sec_idx, moodle_sec in enumerate(moodle_course["sections"], 1):
            # Match to HUB section
            hub_section = match_section(moodle_sec["title"], hub_sections)
            if not hub_section:
                sec_num = moodle_sec.get("num", "")
                for hs in hub_sections:
                    if f"Модуль {sec_num}" in hs.title:
                        hub_section = hs
                        break

            if not hub_section:
                print(f"\n  SKIP section (no match): {moodle_sec['title']}")
                continue

            module_prefix = f"module_{sec_idx:02d}"
            print(f"\n  [{module_prefix}] {moodle_sec['title']}")
            print(f"    -> HUB: {hub_section.title}")

            # Collect video URL and files from all activities in this section
            video_url = None
            file_list = []
            for act in moodle_sec["activities"]:
                if act["video_url"] and not video_url:
                    video_url = act["video_url"]
                for f_info in act["files"]:
                    file_list.append(f_info)

            # --- Download video ---
            if video_url:
                video_filename = f"{module_prefix}_{sanitize(hub_section.title)}.mp4"
                video_path = videos_dir / video_filename

                print(f"  Downloading video: {video_url}")
                ok = download_youtube(video_url, video_path)

                if ok:
                    stats["videos_ok"] += 1
                    # Update DB: find the video activity for this section
                    video_act = hub_section.activities.filter(
                        activity_type__in=["video", "folder", "lesson"],
                        is_visible=True,
                    ).first()
                    if video_act:
                        resource, _ = Resource.objects.get_or_create(activity=video_act)
                        # Save as Django file field relative path (keep under 100 chars)
                        relative_path = f"courses/{slug}/videos/{video_filename}"
                        if len(relative_path) > 100:
                            video_filename = f"{module_prefix}.mp4"
                            relative_path = f"courses/{slug}/videos/{video_filename}"
                        resource.file.name = relative_path
                        resource.file_type = "video/mp4"
                        resource.file_size = video_path.stat().st_size
                        # Keep external_url as backup
                        if not resource.external_url:
                            resource.external_url = video_url
                        resource.save()
                        print(f"    DB updated: {video_act.title}")
                else:
                    stats["videos_fail"] += 1

            # --- Download materials ---
            if file_list:
                mat_act = hub_section.activities.filter(
                    activity_type__in=["resource", "document"],
                    is_visible=True,
                ).first()

                for f_idx, f_info in enumerate(file_list, 1):
                    f_url = f_info["url"]
                    f_name = f_info.get("name", "")

                    # Extract filename from decoded URL path (last segment only)
                    if not f_name or len(f_name) < 3:
                        parsed = urlparse(f_url)
                        f_name = unquote(parsed.path.split("/")[-1])

                    # Strip query string from name
                    f_name = re.sub(r'\?.*$', '', f_name)

                    # Get extension before sanitizing
                    ext = ""
                    if '.' in f_name:
                        ext = f_name.rsplit('.', 1)[-1][:10]
                        base = f_name.rsplit('.', 1)[0]
                    else:
                        base = f_name
                        # Try from URL
                        url_path = unquote(urlparse(f_url).path)
                        if '.' in url_path.split('/')[-1]:
                            ext = url_path.split('/')[-1].rsplit('.', 1)[-1][:10]
                        else:
                            ext = "pdf"

                    safe_base = sanitize(base, 60)
                    safe_name = f"{module_prefix}_{f_idx:02d}_{safe_base}.{ext}"

                    mat_path = materials_dir / safe_name

                    print(f"  Downloading material: {f_name[:60]}")
                    ok = download_moodle_file(moodle_session, f_url, mat_path)

                    if ok:
                        stats["files_ok"] += 1
                    else:
                        stats["files_fail"] += 1

                # Update DB for first material activity
                if mat_act:
                    mat_files = sorted(materials_dir.glob(f"{module_prefix}_*"))
                    if mat_files:
                        resource, _ = Resource.objects.get_or_create(activity=mat_act)
                        first_file = mat_files[0]
                        # Keep path under 100 chars for FileField
                        rel = f"courses/{slug}/materials/{first_file.name}"
                        if len(rel) > 100:
                            short_name = first_file.name[:60] + first_file.suffix
                            rel = f"courses/{slug}/materials/{short_name}"
                        resource.file.name = rel
                        ext = first_file.suffix.lstrip('.')
                        resource.file_type = ext
                        resource.file_size = first_file.stat().st_size
                        resource.save()
                        print(f"    DB updated material: {mat_act.title} ({len(mat_files)} files)")

    # Summary
    print(f"\n\n{'='*60}")
    print(f"DOWNLOAD COMPLETE")
    print(f"  Videos:    {stats['videos_ok']} OK, {stats['videos_fail']} failed")
    print(f"  Materials: {stats['files_ok']} OK, {stats['files_fail']} failed")
    print(f"{'='*60}")

    # Print directory structure
    print(f"\nDirectory structure:")
    for course_dir in sorted(MEDIA_ROOT.iterdir()):
        if not course_dir.is_dir():
            continue
        vids = list((course_dir / "videos").glob("*")) if (course_dir / "videos").exists() else []
        mats = list((course_dir / "materials").glob("*")) if (course_dir / "materials").exists() else []
        print(f"\n  {course_dir.name}/")
        if vids:
            print(f"    videos/ ({len(vids)} files)")
            for v in sorted(vids)[:3]:
                size = v.stat().st_size / 1024 / 1024
                print(f"      {v.name} ({size:.1f} MB)")
            if len(vids) > 3:
                print(f"      ... and {len(vids) - 3} more")
        if mats:
            print(f"    materials/ ({len(mats)} files)")
            for m in sorted(mats)[:3]:
                size = m.stat().st_size / 1024
                print(f"      {m.name} ({size:.1f} KB)")
            if len(mats) > 3:
                print(f"      ... and {len(mats) - 3} more")


if __name__ == "__main__":
    main()
