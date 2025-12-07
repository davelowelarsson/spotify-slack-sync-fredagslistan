from __future__ import annotations

from utils.spotify_access_token import get_spotify_access_token
from utils.texts import (
    PLAYLIST_NAME_PATTERN,
    get_random_playlist_name,
    get_random_playlist_description,
)
from datetime import datetime, timedelta, timezone
from spotipy import SpotifyException
import re
from typing import Optional
from collections import Counter


def get_current_year() -> int:
    """Get the current year."""
    return datetime.now(tz=timezone.utc).year


def generate_playlist_name(year: Optional[int] = None) -> str:
    """
    Generate a random playlist name for a given year.
    
    Args:
        year: The year for the playlist. Defaults to current year.
    
    Returns:
        Random playlist name containing 'Fredagslistan' and the year
    """
    if year is None:
        year = get_current_year()
    return get_random_playlist_name(year)


def generate_playlist_description(year: Optional[int] = None) -> str:
    """
    Generate a random playlist description for a given year.
    
    Args:
        year: The year for the playlist. Defaults to current year.
    
    Returns:
        Random playlist description with the year
    """
    if year is None:
        year = get_current_year()
    return get_random_playlist_description(year)


def extract_year_from_playlist_name(name: str) -> Optional[int]:
    """
    Extract the year from a playlist name.
    
    Matches any playlist starting with 'Fredagslistan' followed by a year.
    
    Args:
        name: Playlist name to parse
    
    Returns:
        The year as an integer, or None if the name doesn't match the pattern
    """
    match = re.match(PLAYLIST_NAME_PATTERN, name)
    if match:
        return int(match.group(1))
    return None


def find_playlist_by_year(year: Optional[int] = None) -> Optional[dict]:
    """
    Find a Fredagslistan playlist for a specific year.
    
    Searches through the current user's playlists to find one matching
    the naming convention 'Fredagslistan YYYY' (with any suffix).
    
    Args:
        year: The year to search for. Defaults to current year.
    
    Returns:
        Playlist dict with id, name, url, and description, or None if not found
    """
    if year is None:
        year = get_current_year()

    sp = get_spotify_access_token()

    # Paginate through all user playlists
    offset = 0
    limit = 50

    while True:
        results = sp.current_user_playlists(limit=limit, offset=offset)
        playlists = results.get('items', [])

        if not playlists:
            break

        for playlist in playlists:
            # Check if this playlist matches the year using pattern matching
            playlist_year = extract_year_from_playlist_name(playlist['name'])
            if playlist_year == year:
                return {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'url': playlist['external_urls']['spotify'],
                    'description': playlist.get('description', '')
                }

        # Check if there are more playlists
        if results.get('next') is None:
            break

        offset += limit

    return None


def create_yearly_playlist(year: Optional[int] = None) -> dict:
    """
    Create a new Fredagslistan playlist for a specific year.
    
    Args:
        year: The year for the playlist. Defaults to current year.
    
    Returns:
        Playlist dict with id, name, url, and description
    """
    if year is None:
        year = get_current_year()

    sp = get_spotify_access_token()
    user_id = sp.current_user()['id']

    name = generate_playlist_name(year)
    description = generate_playlist_description(year)

    print(f"Creating new playlist: {name}")

    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=True,
        collaborative=False,
        description=description
    )

    print(f"Created playlist: {playlist['name']} ({playlist['id']})")
    print(f"URL: {playlist['external_urls']['spotify']}")

    return {
        'id': playlist['id'],
        'name': playlist['name'],
        'url': playlist['external_urls']['spotify'],
        'description': description
    }


def get_or_create_yearly_playlist(year: Optional[int] = None) -> tuple[dict, bool]:
    """
    Get the playlist for a year, creating it if it doesn't exist.
    
    This is the main entry point for the lazy playlist creation pattern.
    
    Args:
        year: The year for the playlist. Defaults to current year.
    
    Returns:
        Tuple of (playlist_dict, was_created) where was_created is True
        if the playlist was newly created, False if it already existed
    """
    if year is None:
        year = get_current_year()

    # Try to find existing playlist
    existing = find_playlist_by_year(year)
    if existing:
        print(f"Found existing playlist: {existing['name']}")
        return existing, False

    # Create new playlist
    print(f"No playlist found for {year}, creating new one...")
    new_playlist = create_yearly_playlist(year)
    return new_playlist, True


def is_track_within_window(added_at: str, days_back: int = 6) -> bool:
    """
    Check if a track was added to the playlist within the rolling window.
    
    Args:
        added_at: ISO 8601 timestamp string (e.g., '2022-01-07T12:00:00Z')
        days_back: Number of days to look back (default: 6)
    
    Returns:
        True if the track was added within the last `days_back` days
    """
    # Parse the added_at timestamp (format: 2022-01-07T12:00:00Z) as UTC
    track_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))

    # Calculate the cutoff date (start of day, days_back days ago) in UTC
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=days_back)
    cutoff_start_of_day = cutoff.replace(
        hour=0, minute=0, second=0, microsecond=0)

    return track_datetime >= cutoff_start_of_day


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


def get_playlist_stats(playlist_id: str) -> dict:
    """
    Get statistics for a playlist including track count, top artists, and top genres.
    
    Args:
        playlist_id: Spotify playlist ID
    
    Returns:
        Dict with track_count, top_artists, and top_genres
    """
    sp = get_spotify_access_token()

    # Get all tracks from the playlist
    all_tracks = []
    artist_ids = []
    artist_counts = Counter()

    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            if item['track'] is None:
                continue  # Skip deleted/unavailable tracks

            track = item['track']
            all_tracks.append(track)

            # Count artist appearances
            for artist in track.get('artists', []):
                artist_counts[artist['name']] += 1
                if artist.get('id'):
                    artist_ids.append(artist['id'])

        if results.get('next') is None:
            break

        try:
            results = sp.next(results)
        except SpotifyException:
            break

    # Get top artists
    top_artists = [artist for artist, _ in artist_counts.most_common(10)]

    # Get genres from artists (Spotify tracks don't have genres, artists do)
    genre_counts = Counter()

    # Fetch artist details in batches of 50 (Spotify API limit)
    unique_artist_ids = list(set(artist_ids))
    for i in range(0, len(unique_artist_ids), 50):
        batch = unique_artist_ids[i:i+50]
        try:
            artists_data = sp.artists(batch)
            for artist in artists_data.get('artists', []):
                if artist:
                    for genre in artist.get('genres', []):
                        genre_counts[genre] += 1
        except SpotifyException:
            continue

    top_genres = [genre for genre, _ in genre_counts.most_common(10)]

    return {
        'track_count': len(all_tracks),
        'top_artists': top_artists,
        'top_genres': top_genres,
    }


def get_previous_year_stats(year: Optional[int] = None) -> Optional[dict]:
    """
    Get stats from the previous year's playlist.
    
    Args:
        year: The current year (will get stats for year-1). Defaults to current year.
    
    Returns:
        Dict with track_count, top_artists, top_genres, and year, or None if no playlist found
    """
    if year is None:
        year = get_current_year()

    previous_year = year - 1

    # Find last year's playlist
    previous_playlist = find_playlist_by_year(previous_year)
    if not previous_playlist:
        print(f"No playlist found for {previous_year}")
        return None

    print(
        f"Getting stats for {previous_year} playlist: {previous_playlist['name']}")

    stats = get_playlist_stats(previous_playlist['id'])
    stats['year'] = previous_year
    stats['playlist_name'] = previous_playlist['name']
    stats['playlist_url'] = previous_playlist['url']

    return stats
