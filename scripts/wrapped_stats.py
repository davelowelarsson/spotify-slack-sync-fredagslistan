"""Read-only "wrapped" stats for the fredagslistan write-up.

Prints AGGREGATE stats only — no names, no leaderboard, and it NEVER writes:
no playlist edits, no Slack posts. It only calls read endpoints
(sp.playlist / playlist_tracks / artists, conversations_history, users_info).

Run locally with your .env loaded:

    uv run python scripts/wrapped_stats.py            # last 3 years
    uv run python scripts/wrapped_stats.py 2022 2026  # explicit range

Note: the per-year contributor count scans a full year of Slack history, so a
multi-year run makes a lot of API calls. Fine for a one-off; don't cron it.
"""

from __future__ import annotations

import json
import os
import sys

# Make the repo root importable when run directly (python scripts/wrapped_stats.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.slack_util import get_year_contributors
from utils.spotify_util import (
    SearchOutcome,
    find_playlist_by_year,
    get_current_year,
    get_playlist_stats,
)

CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "CAB3JFSQN")


def year_stats(year: int) -> dict | None:
    """Aggregate stats for one year, or None if no playlist exists for it."""
    result = find_playlist_by_year(year)
    if result.outcome is not SearchOutcome.FOUND or result.candidate is None:
        print(f"  (no playlist found for {year})", file=sys.stderr)
        return None

    playlist = result.candidate
    stats = get_playlist_stats(playlist["id"])

    # Aggregate-only contributor signal: a high limit returns everyone, and we
    # keep the COUNT + total shares — never the names.
    contributors = get_year_contributors(CHANNEL_ID, year, limit=10_000)

    return {
        "year": year,
        "playlist": playlist["name"],
        "tracks": stats["track_count"],
        "top_genres": stats["top_genres"][:5],
        "top_artists": stats["top_artists"][:5],
        "contributors": len(contributors),
        "slack_shares": sum(c["track_count"] for c in contributors),
    }


def main() -> None:
    current = get_current_year()
    if len(sys.argv) == 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    else:
        start, end = current - 2, current

    years = [y for y in range(start, end + 1)]
    results = [s for y in years if (s := year_stats(y)) is not None]

    totals = {
        "years_covered": len(results),
        "total_tracks": sum(r["tracks"] for r in results),
        "total_slack_shares": sum(r["slack_shares"] for r in results),
        "peak_year_contributors": max((r["contributors"] for r in results), default=0),
        "biggest_year_tracks": max((r["tracks"] for r in results), default=0),
    }

    print(json.dumps({"years": results, "totals": totals}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
