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
from datetime import datetime

# Load .env file
load_dotenv()


def get_slack_client():
    # Get the Slack token from the environment variable
    slack_token = os.getenv("SLACK_API_TOKEN")

    # Instantiate a Web API client
    client = WebClient(token=slack_token)

    return slack_token, client

def check_slack_token():
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


def is_message_from_today(message: dict) -> bool:
    """Check if a message was posted today based on its timestamp."""
    message_date = datetime.fromtimestamp(
        int(message['ts'].split(".")[0])).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    return message_date == today


def get_todays_slack_urls(channel_id="CAB3JFSQN"):
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

    # Process each message from today
    for message in messages:
        if not is_message_from_today(message):
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
                    if is_message_from_today(thread_message):
                        thread_track_ids = extract_spotify_track_ids(
                            thread_message.get('text', ''))
                        for track_id in thread_track_ids:
                            add_track(track_id, thread_message['ts'])
            except Exception as e:
                print(f"Error fetching thread replies: {e}")

    return spotify_links
