#!/usr/bin/env python3
"""Parse data.rss and archive each new item as a JSON file under items/.

Deduplication is keyed on each item's RSS <guid>. Already-archived guids are
discovered by scanning existing JSON files, so re-running is safe and never
produces duplicates even if an item's title is later edited upstream.

Standard library only -- no third-party dependencies.
"""
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

FEED_FILE = Path("data.rss")
ITEMS_DIR = Path("items")

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def text(item, tag):
    el = item.find(tag, NS)
    return el.text.strip() if el is not None and el.text else None


def categories(item):
    return [c.text.strip() for c in item.findall("category") if c.text and c.text.strip()]


def slugify(value):
    # Normalize fancy punctuation (curly quotes, dashes) to ASCII.
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:60].strip("-") or "item"


def existing_guids():
    guids = set()
    for path in ITEMS_DIR.rglob("*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if data.get("guid"):
                guids.add(data["guid"])
        except (json.JSONDecodeError, OSError):
            continue
    return guids


def parse_date(raw):
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def unique_path(directory, base):
    candidate = directory / f"{base}.json"
    n = 2
    while candidate.exists():
        candidate = directory / f"{base}-{n}.json"
        n += 1
    return candidate


def main():
    if not FEED_FILE.exists():
        print(f"::error::{FEED_FILE} not found", file=sys.stderr)
        return 1

    root = ET.parse(FEED_FILE).getroot()
    items = root.findall(".//item")
    if not items:
        print("::error::No <item> elements found in feed", file=sys.stderr)
        return 1

    seen = existing_guids()
    fetched_at = datetime.now(timezone.utc).isoformat()
    new_count = 0

    for item in items:
        guid = text(item, "guid") or text(item, "link")
        if not guid:
            continue
        if guid in seen:
            continue
        seen.add(guid)  # guard against duplicates within a single feed

        published = parse_date(text(item, "pubDate"))
        date_for_path = published or datetime.now(timezone.utc)
        title = text(item, "title") or "untitled"

        record = {
            "guid": guid,
            "title": title,
            "link": text(item, "link"),
            "author": text(item, "dc:creator"),
            "published": published.isoformat() if published else None,
            "categories": categories(item),
            "summary": text(item, "description"),
            "content": text(item, "content:encoded"),
            "fetched_at": fetched_at,
        }

        directory = ITEMS_DIR / f"{date_for_path:%Y}" / f"{date_for_path:%m}"
        directory.mkdir(parents=True, exist_ok=True)
        base = f"{date_for_path:%Y-%m-%d}-{slugify(title)}"
        out = unique_path(directory, base)
        with out.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"added {out}")
        new_count += 1

    print(f"{new_count} new item(s) archived")
    return 0


if __name__ == "__main__":
    sys.exit(main())
