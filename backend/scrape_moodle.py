"""
Scrape all video URLs and materials from Moodle LMS at tcchub.kz
"""
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = "https://tcchub.kz"
USERNAME = "dana_kadyrgaliyeva"
PASSWORD = "weg-z8P-WcB-mUY"


def login(session):
    login_page = session.get(f"{BASE}/login/index.php")
    soup = BeautifulSoup(login_page.text, "html.parser")
    token = soup.find("input", {"name": "logintoken"})
    token_val = token["value"] if token else ""
    resp = session.post(
        f"{BASE}/login/index.php",
        data={
            "username": USERNAME,
            "password": PASSWORD,
            "logintoken": token_val,
        },
        allow_redirects=True,
    )
    if "login" in resp.url.lower() and "index.php" in resp.url:
        print("LOGIN FAILED", file=sys.stderr)
        sys.exit(1)
    print("Logged in OK")


def get_enrolled_courses(session):
    """Get all courses from Moodle site (via course listing pages)."""
    courses = []

    # Try /my/ page first for enrolled courses
    resp = session.get(f"{BASE}/my/")
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find course links
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.match(r"https?://tcchub\.kz/course/view\.php\?id=(\d+)", href)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            title = a.get_text(strip=True)
            if title and len(title) > 3:
                courses.append({"id": int(m.group(1)), "title": title, "url": href})

    # Also try the course index
    resp2 = session.get(f"{BASE}/course/index.php")
    soup2 = BeautifulSoup(resp2.text, "html.parser")
    for a in soup2.find_all("a", href=True):
        href = a["href"]
        m = re.match(r"https?://tcchub\.kz/course/view\.php\?id=(\d+)", href)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            title = a.get_text(strip=True)
            if title and len(title) > 3:
                courses.append({"id": int(m.group(1)), "title": title, "url": href})

    return courses


def extract_video_url(soup_element):
    """Extract YouTube/video URL from a mediaplugin or video tag."""
    # Check data-setup-lazy attribute for YouTube
    for video in soup_element.find_all("video"):
        setup = video.get("data-setup-lazy", "")
        if setup:
            try:
                data = json.loads(setup)
                sources = data.get("sources", [])
                for src in sources:
                    if src.get("src"):
                        return src["src"]
            except json.JSONDecodeError:
                pass
        # Check source tags
        for source in video.find_all("source"):
            src = source.get("src", "")
            if src:
                return src
        # Fallback link
        for a in video.find_all("a", class_="mediafallbacklink"):
            return a.get("href", "")

    # Check iframes
    for iframe in soup_element.find_all("iframe"):
        src = iframe.get("src", "")
        if "youtube" in src or "vimeo" in src or "youtu.be" in src:
            return src

    return None


def scrape_course(session, course_id):
    """Scrape a single Moodle course for all modules, videos, and files."""
    resp = session.get(f"{BASE}/course/view.php?id={course_id}")
    soup = BeautifulSoup(resp.text, "html.parser")

    course_title = ""
    h1 = soup.find("h1")
    if h1:
        course_title = h1.get_text(strip=True)

    sections = []

    # Find all sections
    for sec_el in soup.find_all("li", id=re.compile(r"^section-\d+")):
        sec_num = sec_el.get("id", "").replace("section-", "")

        # Section title
        sec_title_el = sec_el.find(
            ["h3", "h4"], class_=re.compile(r"sectionname|section-title")
        )
        if not sec_title_el:
            sec_title_el = sec_el.find("span", class_="hidden")
        sec_title = sec_title_el.get_text(strip=True) if sec_title_el else f"Section {sec_num}"

        if not sec_title or sec_title in ("", "Общее"):
            continue

        activities = []

        # Find all activity links in this section
        for act_el in sec_el.find_all(
            "li", class_=re.compile(r"activity|modtype_")
        ):
            act_link = act_el.find("a", href=True)
            if not act_link:
                continue

            href = act_link["href"]
            act_title = ""
            # Try to get clean title
            inst_name = act_el.find("span", class_="instancename")
            if inst_name:
                act_title = inst_name.get_text(strip=True)
                # Remove access info suffix
                hidden = inst_name.find("span", class_="accesshide")
                if hidden:
                    act_title = act_title.replace(hidden.get_text(), "").strip()
            else:
                act_title = act_link.get_text(strip=True)

            # Determine type from URL
            act_type = "unknown"
            if "/mod/folder/" in href:
                act_type = "folder"
            elif "/mod/resource/" in href:
                act_type = "resource"
            elif "/mod/quiz/" in href:
                act_type = "quiz"
            elif "/mod/assign/" in href:
                act_type = "assignment"
            elif "/mod/url/" in href:
                act_type = "url"
            elif "/mod/page/" in href:
                act_type = "page"
            elif "/mod/forum/" in href:
                act_type = "forum"

            # Extract module ID
            m = re.search(r"id=(\d+)", href)
            mod_id = int(m.group(1)) if m else 0

            activities.append(
                {
                    "id": mod_id,
                    "title": act_title,
                    "type": act_type,
                    "url": href,
                    "video_url": None,
                    "files": [],
                }
            )

        sections.append(
            {"num": sec_num, "title": sec_title, "activities": activities}
        )

    return {"id": course_id, "title": course_title, "sections": sections}


def scrape_activity_content(session, activity):
    """Fetch an individual activity page to extract video URLs and file links."""
    if activity["type"] not in ("folder", "resource", "url", "page"):
        return

    resp = session.get(activity["url"])
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract video
    video_url = extract_video_url(soup)
    if video_url:
        activity["video_url"] = video_url

    # Extract downloadable files
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "pluginfile.php" in href:
            fname = a.get_text(strip=True) or href.split("/")[-1].split("?")[0]
            activity["files"].append({"name": fname, "url": href})

    # Also check folder tree spans
    tree = soup.find("div", id=re.compile(r"folder_tree"))
    if tree:
        for a in tree.find_all("a", href=True):
            href = a["href"]
            fname_el = a.find("span", class_="fp-filename")
            fname = fname_el.get_text(strip=True) if fname_el else a.get_text(strip=True)
            if fname and href not in [f["url"] for f in activity["files"]]:
                activity["files"].append({"name": fname, "url": href})


def main():
    s = requests.Session()
    login(s)

    print("\nFetching course list...")
    courses = get_enrolled_courses(s)
    print(f"Found {len(courses)} courses")

    if not courses:
        # Try fetching specific known course IDs
        print("Trying known course IDs...")
        for cid in range(1, 20):
            resp = s.get(f"{BASE}/course/view.php?id={cid}")
            if resp.status_code == 200 and "login" not in resp.url:
                soup = BeautifulSoup(resp.text, "html.parser")
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)
                    courses.append({"id": cid, "title": title, "url": f"{BASE}/course/view.php?id={cid}"})
                    print(f"  Found course {cid}: {title}")

    all_data = []
    for course_info in courses:
        print(f"\nScraping: {course_info['title']} (id={course_info['id']})")
        course_data = scrape_course(s, course_info["id"])

        # Now fetch each activity's content
        for section in course_data["sections"]:
            for activity in section["activities"]:
                if activity["type"] in ("folder", "resource", "url", "page"):
                    print(f"  Fetching: {activity['title']} ({activity['type']})")
                    scrape_activity_content(s, activity)
                    if activity["video_url"]:
                        print(f"    VIDEO: {activity['video_url']}")
                    if activity["files"]:
                        print(f"    FILES: {len(activity['files'])}")

        all_data.append(course_data)

    # Save results
    output_path = "/app/moodle_content.json"
    with open(output_path, "w") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n\nSaved to {output_path}")

    # Summary
    total_videos = 0
    total_files = 0
    for course in all_data:
        for section in course["sections"]:
            for act in section["activities"]:
                if act["video_url"]:
                    total_videos += 1
                total_files += len(act["files"])

    print(f"\nSUMMARY: {len(all_data)} courses, {total_videos} videos, {total_files} files")


if __name__ == "__main__":
    main()
