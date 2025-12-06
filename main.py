# start by getting spotify access-token
# import the file and runt the function
from __future__ import annotations

from utils.spotify_util import get_playlist, add_songs_to_spotify_playlist
from utils.slack_util import get_recent_slack_tracks

from datetime import datetime


def compare_lists_and_remove_duplicates() -> list[str]:
    """Compare Slack tracks with Spotify playlist and return new tracks to add."""
    songs_already_in_spotify = get_playlist()
    songs_added_in_slack = get_recent_slack_tracks()

    # compare the two lists and create a new list without duplicates
    # if the song is in the spotify list it's not allowed to be added to the new list

    # create a new list
    songs_to_add = []

    # the lists have different formats which we need to take into account
    # the slack list is a list of dicts with track_id and timestamp
    # the spotify list is a list of dicts with name, url, and track_id

    # count the length of both lists
    print('Tracks from Slack (last 6 days): ', len(songs_added_in_slack))
    print('Tracks already in Spotify playlist: ', len(songs_already_in_spotify))

    # Sort slack tracks by timestamp
    songs_added_in_slack_sorted = sorted(
        songs_added_in_slack, key=lambda x: x['timestamp'])

    # loop through the slack list
    for song in songs_added_in_slack_sorted:
        # check if the song is in the spotify list
        # if it's not in the list, add it to the new list
        if not any(song['track_id'] == s['track_id'] for s in songs_already_in_spotify):
            songs_to_add.append(song['track_id'])

    # print the new list
    print('songs_to_add: ', len(songs_to_add))
    print(songs_to_add)
    return songs_to_add


def main() -> None:
    """Main entry point - sync Slack tracks to Spotify playlist."""
    # get the songs to add to the spotify list
    songs_to_add = compare_lists_and_remove_duplicates()
    # add the songs to the spotify list
    add_songs_to_spotify_playlist(track_ids=songs_to_add)


main()
