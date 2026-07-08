# start by getting spotify access-token
# import the file and runt the function

import os
from datetime import datetime

from utils.playlist_state import is_dry_run, read_state_from_env, write_github_output
from utils.slack_util import (
    announce_new_playlist,
    anonymize_name,
    get_recent_slack_tracks,
    get_year_contributors,
)
from utils.spotify_util import (
    add_songs_to_spotify_playlist,
    get_playlist,
    get_previous_year_stats,
    resolve_yearly_playlist,
)

# Slack channel to sync, configurable via env. Defaults to the #fredagslistan
# production channel; set SLACK_CHANNEL_ID to point elsewhere (e.g. a test
# channel) without changing code.
ACTIVE_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID") or "CAB3JFSQN"


def compare_lists_and_remove_duplicates(playlist_id: str) -> tuple[list[str], list[dict]]:
    """Compare Slack tracks with Spotify playlist and return new tracks to add.

    Args:
        playlist_id: The Spotify playlist ID to compare against

    Returns:
        Tuple of (list of track IDs to add, list of track dicts with full info)
    """
    songs_already_in_spotify = get_playlist(playlist_id=playlist_id)
    songs_added_in_slack = get_recent_slack_tracks(channel_id=ACTIVE_CHANNEL_ID)

    # compare the two lists and create a new list without duplicates
    # if the song is in the spotify list it's not allowed to be added to the new list

    # create lists for tracks to add
    songs_to_add = []
    songs_to_add_full = []  # Full track info including user attribution

    # the lists have different formats which we need to take into account
    # the slack list is a list of dicts with track_id, timestamp, user_id, and user_name
    # the spotify list is a list of dicts with name, url, and track_id

    # count the length of both lists
    print("Tracks from Slack (last 6 days): ", len(songs_added_in_slack))
    print("Tracks already in Spotify playlist: ", len(songs_already_in_spotify))

    # Sort slack tracks by timestamp
    songs_added_in_slack_sorted = sorted(songs_added_in_slack, key=lambda x: x["timestamp"])

    # loop through the slack list
    for song in songs_added_in_slack_sorted:
        # check if the song is in the spotify list
        # if it's not in the list, add it to the new list
        if not any(song["track_id"] == s["track_id"] for s in songs_already_in_spotify):
            songs_to_add.append(song["track_id"])
            songs_to_add_full.append(song)

    # print the new list with user attribution
    print(f"\n📀 Songs to add: {len(songs_to_add)}")
    for song in songs_to_add_full:
        print(f"  🎵 {song['track_id']} (shared by {anonymize_name(song.get('user_name', ''))})")

    return songs_to_add, songs_to_add_full


def main() -> None:
    """Main entry point - sync Slack tracks to Spotify playlist.

    Reads durable state from the environment, resolves the current-year
    playlist without ever creating on uncertainty, runs the sync only when a
    playlist was resolved, announces ONLY when a playlist was actually created,
    then emits the new state to $GITHUB_OUTPUT. The process always exits 0 for
    the counter path — a non-zero exit_code is EMITTED as output so the
    workflow can persist the incremented counter before turning the build red.
    """
    print(f"Starting Fredagslistan sync at {datetime.now().isoformat()}")
    print(f"Using channel: {ACTIVE_CHANNEL_ID}")

    dry_run = is_dry_run()
    if dry_run:
        print("🧪 DRY RUN mode — no writes will be made")

    # Resolve the playlist from durable state (never creates on uncertainty).
    state = read_state_from_env()
    result = resolve_yearly_playlist(state, dry_run=dry_run)

    # Emit state IMMEDIATELY — before any Spotify/Slack writes — so the resolved
    # playlist id and failure counter survive even if a later network call
    # crashes. Otherwise a just-created playlist would be forgotten and could be
    # recreated (and re-announced) on the next run — the very incident this fixes.
    write_github_output(result)

    # UNCERTAIN / ABORTED: do nothing destructive, just return cleanly.
    if result.playlist is None:
        print(
            f"⚠️ No playlist resolved (action={result.action.value}). Skipping sync and announce."
        )
        return

    playlist = result.playlist
    playlist_id = playlist["id"]

    print(f"Using playlist: {playlist['name']} ({playlist_id}) [action={result.action.value}]")

    # Announce ONLY when a playlist was actually created. This is the coupling
    # guarantee: a cache miss / search failure resolves to result.playlist=None
    # above and never reaches this branch. `was_created` is only ever True on a
    # real CREATED action, which cannot happen in dry_run (see WOULD_CREATE
    # above) -- the `not dry_run` guard is kept explicit for clarity.
    if result.was_created and not dry_run:
        print("New playlist created! Announcing in Slack...")

        # Get stats from last year's playlist for the announcement
        print("Fetching previous year stats...")
        previous_year_stats = get_previous_year_stats()

        if previous_year_stats:
            print(f"📊 Previous year ({previous_year_stats['year']}):")
            print(f"   - Tracks: {previous_year_stats['track_count']}")
            print(f"   - Top genres: {previous_year_stats['top_genres'][:5]}")
            print(f"   - Top artists: {previous_year_stats['top_artists'][:5]}")

            # Fetch top contributors from Slack for the previous year
            print("Fetching top contributors from Slack...")
            top_contributors = get_year_contributors(
                channel_id=ACTIVE_CHANNEL_ID, year=previous_year_stats["year"], limit=5
            )
            if top_contributors:
                previous_year_stats["top_contributors"] = top_contributors
                masked = [anonymize_name(c["user_name"]) for c in top_contributors]
                print(f"   - Top contributors: {masked}")
        else:
            print("No previous year playlist found for stats")

        message_posted, topic_updated = announce_new_playlist(
            channel_id=ACTIVE_CHANNEL_ID,
            playlist=playlist,
            previous_year_stats=previous_year_stats,
        )
        if message_posted:
            print("✅ Announcement posted successfully")
        else:
            print("❌ Failed to post announcement")

        if topic_updated:
            print("✅ Channel topic updated successfully")
        else:
            print("❌ Failed to update channel topic")

    # Get the songs to add to the spotify list (read-only: runs in dry_run too).
    songs_to_add, _songs_to_add_full = compare_lists_and_remove_duplicates(playlist_id=playlist_id)

    if dry_run:
        print(f"DRY RUN: would add {len(songs_to_add)} tracks to {playlist['name']}")
    else:
        # Add the songs to the spotify list
        add_songs_to_spotify_playlist(playlist_id=playlist_id, track_ids=songs_to_add)
        print(f"\n✅ Sync complete. Added {len(songs_to_add)} tracks to {playlist['name']}")


if __name__ == "__main__":
    main()
