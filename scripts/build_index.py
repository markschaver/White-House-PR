#!/usr/bin/env python3
"""Build a single index.json manifest of every archived item under items/.

The manifest lets a website load the full list of press releases in one
request (title, link, date, etc.) and lazily fetch an individual item's full
JSON -- via its `path` -- only when needed. The large `content` field is
deliberately omitted to keep the manifest small.

Standard library only -- no third-party dependencies.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ITEMS_DIR = Path("items")
INDEX_FILE = Path("index.json")


def main():
    entries = []
    for path in ITEMS_DIR.rglob("*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"::warning::skipping unreadable {path}", file=sys.stderr)
            continue

        entries.append({
            "guid": data.get("guid"),
            "title": data.get("title"),
            "link": data.get("link"),
            "author": data.get("author"),
            "published": data.get("published"),
            "categories": data.get("categories", []),
            "summary": data.get("summary"),
            "path": path.as_posix(),
        })

    # Newest first; items without a date sort to the end.
    entries.sort(key=lambda e: e.get("published") or "", reverse=True)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "items": entries,
    }

    with INDEX_FILE.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"wrote {INDEX_FILE} with {len(entries)} item(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
