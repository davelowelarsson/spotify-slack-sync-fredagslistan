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
from typing import Optional

from utils.texts import (
    SLACK_TOPIC_TEMPLATES as TOPIC_MESSAGES,
    get_random_topic_message,
    get_random_announcement_header,
    get_random_announcement_body,
    get_random_stats_intro,
    format_top_genres,
    format_top_artists,
    format_top_contributors,
)

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


# Cache for user lookups to avoid repeated API calls
_user_cache: dict[str, str] = {}


def get_user_display_name(client: WebClient, user_id: str) -> str:
    """
    Get the display name for a Slack user.
    
    Uses a cache to avoid repeated API calls for the same user.
    Falls back to user_id if the lookup fails.
    
    Args:
        client: Slack WebClient instance
        user_id: Slack user ID (e.g., 'U012AB3CDE')
    
    Returns:
        User's display name, real name, or user ID as fallback
    """
    # Check cache first
    if user_id in _user_cache:
        return _user_cache[user_id]

    try:
        response = client.users_info(user=user_id)
        if response['ok']:
            user = response['user']
            profile = user.get('profile', {})
            # Prefer display_name, fall back to real_name, then name
            name = (
                profile.get('display_name') or
                profile.get('real_name') or
                user.get('name') or
                user_id
            )
            _user_cache[user_id] = name
            return name
    except SlackApiError as e:
        print(f"Error fetching user info for {user_id}: {e.response['error']}")

    # Fall back to user_id if we can't get the name
    _user_cache[user_id] = user_id
    return user_id


def get_recent_slack_tracks(channel_id: str = "CAB3JFSQN") -> list[dict]:
    """
    Get Spotify track IDs from recent Slack messages (within rolling window).

    Fetches messages from the last 6 days, including thread replies,
    and extracts all Spotify track IDs along with who shared them.

    Args:
        channel_id: Slack channel ID to fetch messages from

    Returns:
        List of dicts with 'track_id', 'timestamp', 'user_id', and 'user_name' keys
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

    def add_track(track_id: str, timestamp: str, user_id: str):
        """Add a track if not already seen, including user attribution."""
        if track_id not in seen_track_ids:
            seen_track_ids.add(track_id)
            user_name = get_user_display_name(
                client, user_id) if user_id else "Unknown"
            spotify_links.append({
                'track_id': track_id,
                'timestamp': timestamp,
                'user_id': user_id,
                'user_name': user_name
            })

    # Process each message within the rolling window
    for message in messages:
        if not is_message_within_window(message):
            continue

        user_id = message.get('user', '')

        # Extract all Spotify track IDs from this message
        track_ids = extract_spotify_track_ids(message.get('text', ''))
        for track_id in track_ids:
            add_track(track_id, message['ts'], user_id)

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
                        thread_user_id = thread_message.get('user', '')
                        thread_track_ids = extract_spotify_track_ids(
                            thread_message.get('text', ''))
                        for track_id in thread_track_ids:
                            add_track(
                                track_id, thread_message['ts'], thread_user_id)
            except SlackApiError as e:
                print(f"Error fetching thread replies: {e.response['error']}")

    return spotify_links


def get_year_contributors(
    channel_id: str,
    year: int,
    limit: int = 5
) -> list[dict]:
    """
    Get top contributors for a specific year from Slack message history.
    
    Scans messages from the entire year to count who shared the most Spotify tracks.
    This is intended for yearly stats and should only be called once per year.
    
    Note: This can make many API calls due to pagination. Use sparingly.
    
    Args:
        channel_id: Slack channel ID to scan
        year: The year to get contributors for
        limit: Number of top contributors to return (default: 5)
    
    Returns:
        List of dicts with 'user_id', 'user_name', and 'track_count' keys,
        sorted by track_count descending
    """
    from collections import Counter
    
    slack_token, client = get_slack_client()
    
    # Calculate start and end timestamps for the year
    start_of_year = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_of_year = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    oldest = str(start_of_year.timestamp())
    latest = str(end_of_year.timestamp())
    
    print(f"Scanning Slack messages from {year} for top contributors...")
    
    user_track_counts: Counter = Counter()
    total_messages = 0
    
    # Paginate through message history
    cursor = None
    while True:
        try:
            kwargs = {
                'channel': channel_id,
                'oldest': oldest,
                'latest': latest,
                'limit': 200,  # Max per request
            }
            if cursor:
                kwargs['cursor'] = cursor
                
            response = client.conversations_history(**kwargs)
            messages = response.get('messages', [])
            
            for message in messages:
                total_messages += 1
                user_id = message.get('user', '')
                
                # Count tracks in this message
                track_ids = extract_spotify_track_ids(message.get('text', ''))
                if track_ids and user_id:
                    user_track_counts[user_id] += len(track_ids)
                
                # Also check thread replies if any
                if message.get('reply_count', 0) > 0:
                    thread_ts = message.get('thread_ts', message['ts'])
                    try:
                        replies = client.conversations_replies(
                            channel=channel_id,
                            ts=thread_ts
                        )
                        for reply in replies.get('messages', [])[1:]:  # Skip parent
                            reply_user = reply.get('user', '')
                            reply_tracks = extract_spotify_track_ids(reply.get('text', ''))
                            if reply_tracks and reply_user:
                                user_track_counts[reply_user] += len(reply_tracks)
                    except SlackApiError:
                        pass  # Skip thread if we can't fetch it
            
            # Check for more pages
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
                
        except SlackApiError as e:
            print(f"Error fetching message history: {e.response['error']}")
            break
    
    print(f"Scanned {total_messages} messages, found {sum(user_track_counts.values())} track shares")
    
    # Get top contributors and resolve their names
    top_contributors = []
    for user_id, track_count in user_track_counts.most_common(limit):
        user_name = get_user_display_name(client, user_id)
        top_contributors.append({
            'user_id': user_id,
            'user_name': user_name,
            'track_count': track_count
        })
    
    return top_contributors


# Re-export get_random_topic_message from texts module for backward compatibility
# The actual implementation is now in utils/texts.py


def update_channel_topic(channel_id: str, topic: str) -> bool:
    """
    Update the topic of a Slack channel.
    
    Args:
        channel_id: The Slack channel ID
        topic: The new topic text
    
    Returns:
        True if successful, False otherwise
    """
    slack_token, client = get_slack_client()

    try:
        response = client.conversations_setTopic(
            channel=channel_id,
            topic=topic
        )
        if response["ok"]:
            print(f"Successfully updated channel topic to: {topic}")
            return True
        else:
            print(f"Failed to update channel topic: {response}")
            return False
    except SlackApiError as e:
        print(f"Error updating channel topic: {e.response['error']}")
        return False


def post_playlist_announcement(
    channel_id: str,
    playlist_name: str,
    playlist_url: str,
    year: int,
    previous_year_stats: Optional[dict] = None
) -> bool:
    """
    Post a playlist announcement message to Slack using Block Kit.
    
    Args:
        channel_id: The Slack channel ID to post to
        playlist_name: The name of the playlist
        playlist_url: The Spotify playlist URL
        year: The playlist year
        previous_year_stats: Optional dict with stats from previous year
            (track_count, top_artists, top_genres, year)
    
    Returns:
        True if successful, False otherwise
    """
    slack_token, client = get_slack_client()

    # Get dynamic texts
    header_text = get_random_announcement_header(year)
    body_text = get_random_announcement_body()

    # Build Block Kit message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{body_text}\n\n*{playlist_name}*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Dela Spotify-låtar i den här kanalen så läggs de automatiskt till i listan. Kör hårt! 🚀"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🎧 Öppna i Spotify",
                        "emoji": True
                    },
                    "url": playlist_url,
                    "action_id": "open_spotify_playlist"
                }
            ]
        },
    ]

    # Add previous year stats if available
    if previous_year_stats and previous_year_stats.get('track_count', 0) > 0:
        playlist_name = previous_year_stats.get(
            'playlist_name', f"Fredagslistan {previous_year_stats['year']}")
        stats_intro = get_random_stats_intro(
            playlist_name,
            previous_year_stats['track_count']
        )

        stats_blocks = [
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Från förra listan:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": stats_intro
                }
            },
        ]

        # Add top genres if available
        if previous_year_stats.get('top_genres'):
            genres_text = format_top_genres(
                previous_year_stats['top_genres'], limit=5)
            stats_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Topgenrer:* {genres_text}"
                }
            })

        # Add top artists if available
        if previous_year_stats.get('top_artists'):
            artists_text = format_top_artists(
                previous_year_stats['top_artists'], limit=5)
            stats_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Topartister:* {artists_text}"
                }
            })

        # Add top contributors if available
        if previous_year_stats.get('top_contributors'):
            contributors_text = format_top_contributors(
                previous_year_stats['top_contributors'], limit=5)
            stats_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Mest aktiva bidragsgivare:* {contributors_text}"
                }
            })

        # Add link to previous year's playlist
        if previous_year_stats.get('playlist_url'):
            stats_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<{previous_year_stats['playlist_url']}|🎵 Lyssna på {previous_year_stats['year']} års lista>"
                    }
                ]
            })

        blocks.extend(stats_blocks)

    # Add footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Skapad automatiskt av Fredagslistan-boten • {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}"
            }
        ]
    })

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            # Fallback text
            text=f"🎉 Ny Fredagslista för {year}! {playlist_url}",
            blocks=blocks
        )
        if response["ok"]:
            print(
                f"Successfully posted playlist announcement to channel {channel_id}")
            return True
        else:
            print(f"Failed to post announcement: {response}")
            return False
    except SlackApiError as e:
        print(f"Error posting announcement: {e.response['error']}")
        return False


def announce_new_playlist(
    channel_id: str,
    playlist: dict,
    year: Optional[int] = None,
    previous_year_stats: Optional[dict] = None
) -> tuple[bool, bool]:
    """
    Announce a new playlist by posting a message and updating the channel topic.
    
    Args:
        channel_id: The Slack channel ID
        playlist: Playlist dict with 'name', 'url', 'id', 'description'
        year: The playlist year (defaults to current year)
        previous_year_stats: Optional dict with stats from previous year
    
    Returns:
        Tuple of (message_posted, topic_updated) booleans
    """
    if year is None:
        year = datetime.now(tz=timezone.utc).year

    # Post announcement message
    message_posted = post_playlist_announcement(
        channel_id=channel_id,
        playlist_name=playlist['name'],
        playlist_url=playlist['url'],
        year=year,
        previous_year_stats=previous_year_stats
    )

    # Update channel topic
    topic = get_random_topic_message(year, playlist['url'])
    topic_updated = update_channel_topic(channel_id, topic)

    return message_posted, topic_updated
