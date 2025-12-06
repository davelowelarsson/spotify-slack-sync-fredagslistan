from utils.spotify_access_token import get_spotify_access_token
from datetime import datetime, timedelta
from spotipy import SpotifyException


def is_track_within_window(added_at: str, days_back: int = 6) -> bool:
    """
    Check if a track was added to the playlist within the rolling window.
    
    Args:
        added_at: ISO 8601 timestamp string (e.g., '2022-01-07T12:00:00Z')
        days_back: Number of days to look back (default: 6)
    
    Returns:
        True if the track was added within the last `days_back` days
    """
    # Parse the added_at timestamp (format: 2022-01-07T12:00:00Z)
    track_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
    track_date = track_datetime.replace(tzinfo=None)

    # Calculate the cutoff date
    now = datetime.now()
    cutoff = now - timedelta(days=days_back)
    cutoff_start_of_day = cutoff.replace(
        hour=0, minute=0, second=0, microsecond=0)

    return track_date >= cutoff_start_of_day


def get_playlist(playlist_id='1OdSuwMRWtpP0nVhLffEqe', days_back: int = 6):
    """
    Get tracks added to the Spotify playlist within the rolling window.
    
    Only returns tracks added in the last `days_back` days. This allows
    songs that were added more than 6 days ago to "come back" if someone
    shares them again in Slack.
    
    Args:
        playlist_id: Spotify playlist ID
        days_back: Number of days to look back (default: 6)
    
    Returns:
        List of track dicts with name, url, and track_id
    """
    sp = get_spotify_access_token()

    playlist = sp.playlist(playlist_id)
    print(playlist['name'])
    print(playlist['description'])
    print(playlist['external_urls'])

    # Get tracks added within the rolling window
    recent_songs = []

    results = playlist['tracks']
    while results:
        for item in results['items']:
            # Only include tracks added within the rolling window
            if is_track_within_window(item['added_at'], days_back):
                recent_songs.append({
                    'name': item['track']['name'],
                    'url': item['track']['external_urls']['spotify'],
                    'track_id': item['track']['id']
                })

        if results['next'] is None:
            break

        try:
            results = sp.next(results)
        except SpotifyException:
            results = None

    return recent_songs


# Add tracks to playlist using track id
def add_songs_to_spotify_playlist(playlist_id='1OdSuwMRWtpP0nVhLffEqe', track_ids=[]):
    sp = get_spotify_access_token()

    # print('######### Adding tracks to playlist: ###########')
    # print(sp.me())
    # print('sp access token: ', sp.auth_manager.get_access_token())

    # make sure the incoming tracks is a list with strings
    if not isinstance(track_ids, list):
        track_ids = [track_ids]

    if track_ids:
        # print('Adding tracks: ', track_ids)
        sp.playlist_add_items(playlist_id, track_ids)
    else:
        print('No tracks to add to playlist.')
