# this function will check a channel in a slack workspace for messages containing spotify links.
# it will return a list of spotiyfy links
# these links will be compared in a later function to a spotify playlist

# access slack channel
# get messages from slack channel
# check if message contains spotify link
# if yes, add to list
# return list

from __future__ import annotations

# import the slack client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta, timezone

# Load .env file
load_dotenv()


def get_slack_client() -> tuple[str | None, WebClient]:
    """Get Slack client and token from environment."""
    # Get the Slack token from the environment variable
    slack_token = os.getenv("SLACK_API_TOKEN")

    # Instantiate a Web API client
    client = WebClient(token=slack_token)

    return slack_token, client


def check_slack_token() -> None:
    slack_token, client = get_slack_client()

    try:
        response = client.auth_test()
        if response["ok"]:
            print("Slack token is valid.")
        else:
            print("Slack token is invalid.")
    except SlackApiError as e:
        print(f"Error validating Slack token: {e.response['error']}")


def extract_spotify_track_ids(text: str) -> list[str]:
    """
    Extract all Spotify track IDs from a text string.

    Handles various URL formats:
    - https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN
    - https://open.spotify.com/track/IT/32M0hVHxSzweqkrIJOxJqN (with country code)
    - https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN?si=abc123 (with query params)

    Returns a list of track IDs found in the text.
    """
    # Pattern explanation:
    # - track/ followed by optional 2-letter country code and slash
    # - then capture the track ID (alphanumeric, typically 22 chars)
    # - stops at ? or whitespace or end of string
    pattern = r'open\.spotify\.com/track/(?:[A-Z]{2}/)?([a-zA-Z0-9]+)'
    return re.findall(pattern, text)


def is_message_within_window(message: dict, days_back: int = 6) -> bool:
    """
    Check if a message was posted within the rolling window.

    Args:
        message: A Slack message dict with a 'ts' timestamp field
        days_back: Number of days to look back (default: 6 to skip last Friday)

    Returns:
        True if the message is from today or within the last `days_back` days
    """
    message_timestamp = int(message['ts'].split(".")[0])
    # Convert Unix timestamp to UTC datetime
    message_datetime = datetime.fromtimestamp(message_timestamp, tz=timezone.utc)

    # Calculate the cutoff date (start of day, days_back days ago) in UTC
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=days_back)
    cutoff_start_of_day = cutoff.replace(
        hour=0, minute=0, second=0, microsecond=0)

    return message_datetime >= cutoff_start_of_day


def get_recent_slack_tracks(channel_id: str = "CAB3JFSQN") -> list[dict]:
    """
    Get Spotify track IDs from recent Slack messages (within rolling window).

    Fetches messages from the last 6 days, including thread replies,
    and extracts all Spotify track IDs.

    Args:
        channel_id: Slack channel ID to fetch messages from

    Returns:
        List of dicts with 'track_id' and 'timestamp' keys
    """
    slack_token, client = get_slack_client()

    check_slack_token()

    # get the messages from the #fredagslistan channel
    response = client.conversations_history(
        channel=channel_id
    )

    # retrieve the messages
    messages = response['messages']

    # Track all spotify links found (using set to avoid duplicates)
    seen_track_ids = set()
    spotify_links = []

    def add_track(track_id, timestamp):
        """Add a track if not already seen."""
        if track_id not in seen_track_ids:
            seen_track_ids.add(track_id)
            spotify_links.append({
                'track_id': track_id,
                'timestamp': timestamp
            })

    # Process each message within the rolling window
    for message in messages:
        if not is_message_within_window(message):
            continue

        # Extract all Spotify track IDs from this message
        track_ids = extract_spotify_track_ids(message.get('text', ''))
        for track_id in track_ids:
            add_track(track_id, message['ts'])

        # Check if this message has thread replies
        reply_count = message.get('reply_count', 0)
        if reply_count > 0:
            # Fetch thread replies
            thread_ts = message.get('thread_ts', message['ts'])
            try:
                replies_response = client.conversations_replies(
                    channel=channel_id,
                    ts=thread_ts
                )
                thread_messages = replies_response.get('messages', [])

                # Process thread messages (skip first one as it's the parent, already processed)
                for thread_message in thread_messages[1:]:
                    if is_message_within_window(thread_message):
                        thread_track_ids = extract_spotify_track_ids(
                            thread_message.get('text', ''))
                        for track_id in thread_track_ids:
                            add_track(track_id, thread_message['ts'])
            except SlackApiError as e:
                print(f"Error fetching thread replies: {e.response['error']}")

    return spotify_links
