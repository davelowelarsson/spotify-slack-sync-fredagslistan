"""Read-only: show the OLDEST messages in the Slack channel (for acknowledgements).

Fetches the channel history, sorts oldest-first, and prints the first N with
date, author, and text. Read endpoints only (conversations_history + users_info)
— no writes, no posting.

    uv run python scripts/first_messages.py         # oldest 20
    uv run python scripts/first_messages.py 40      # oldest 40
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

# Make the repo root importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk.errors import SlackApiError

from utils.slack_util import get_slack_client, get_user_display_name

CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "CAB3JFSQN")
MAX_PAGES = 300


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    _token, client = get_slack_client()

    messages: list[dict] = []
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        kwargs: dict = {"channel": CHANNEL_ID, "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        try:
            resp = client.conversations_history(**kwargs)
        except SlackApiError as e:
            print(f"Error fetching history: {e.response['error']}", file=sys.stderr)
            break
        messages.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    messages.sort(key=lambda m: float(m["ts"]))
    print(f"Fetched {len(messages)} messages. Oldest {n}:\n")
    for m in messages[:n]:
        when = datetime.fromtimestamp(float(m["ts"]), tz=UTC).strftime("%Y-%m-%d %H:%M")
        user_id = m.get("user", "")
        who = get_user_display_name(client, user_id) if user_id else (m.get("subtype") or "system")
        text = (m.get("text", "") or "").replace("\n", " ")
        print(f"{when}  {who}: {text[:240]}")


if __name__ == "__main__":
    main()
