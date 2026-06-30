# White House Press Releases Archive

Archive of press releases published by
[The White House](https://www.whitehouse.gov/releases/). A scheduled GitHub
Action fetches the official RSS feed every 15 minutes, saves the latest
snapshot, and permanently stores each new release as an individual JSON file —
building a deduplicated, browsable history over time.

## How it works

The workflow in [`.github/workflows/flat.yml`](.github/workflows/flat.yml) runs
on a 15-minute schedule (and can be triggered manually) and performs these steps:

1. **Fetch** the White House releases RSS feed
   (`https://www.whitehouse.gov/releases/feed/`) into [`data.rss`](data.rss).
2. **Validate** that the response is real RSS, failing the run loudly if not.
3. **Archive** new items by running
   [`scripts/ingest_rss.py`](scripts/ingest_rss.py), which parses the feed and
   writes any previously unseen releases as JSON files.
4. **Commit and push** `data.rss` and any new items back to the repository.

## Files

| Path | Description |
| --- | --- |
| [`data.rss`](data.rss) | The most recent snapshot of the raw RSS feed (overwritten each run). |
| `items/` | The permanent archive — one JSON file per release, organized by year and month. |
| [`scripts/ingest_rss.py`](scripts/ingest_rss.py) | Parses `data.rss` and writes new items as JSON (Python standard library only). |
| [`.github/workflows/flat.yml`](.github/workflows/flat.yml) | The scheduled GitHub Action that drives everything. |

## Archive

Each release is stored at:

```
items/<YYYY>/<MM>/<YYYY-MM-DD>-<title-slug>.json
```

For example:

```
items/2026/06/2026-06-30-trump-administration-nepa-reforms-a-win-for-all-americans.json
```

Every JSON file contains:

| Field | Description |
| --- | --- |
| `guid` | The feed's unique identifier for the item (used for deduplication). |
| `title` | The release title. |
| `link` | URL of the full release on whitehouse.gov. |
| `author` | The originating author (e.g. "The White House"). |
| `published` | Publication timestamp (ISO 8601, UTC). |
| `categories` | List of category tags from the feed. |
| `summary` | The item's `<description>` (HTML). |
| `content` | The item's full `<content:encoded>` body (HTML). |
| `fetched_at` | When this item was archived (ISO 8601, UTC). |

### Deduplication

The RSS feed only exposes the most recent items at any time. To build a
complete history without duplicates, `ingest_rss.py` keys on each item's
`guid`: before writing, it scans the existing archive and skips any item whose
`guid` has already been saved. Re-running the script is therefore always safe.

## Running locally

The ingest script has no third-party dependencies. With a `data.rss` file
present, run:

```bash
python3 scripts/ingest_rss.py
```

It prints each newly archived item and a count of how many were added.
