# Prepare spotify access
# export function to be used in main.py
#
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import requests
import threading

# Load environment variables from .env file (if exists)
# Spotipy reads SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI automatically
load_dotenv()

# Cached Spotify client instance (singleton pattern)
_spotify_client: spotipy.Spotify | None = None
_token_validated: bool = False
_lock = threading.Lock()


def check_spotify_token(spotify_token):
    spotify_token = spotify_token or os.getenv("SPOTIFY_API_TOKEN")

    # print('Spotify token: ', spotify_token)
    # print('Spotify token access_token: ', spotify_token.get('access_token'))

    headers = {
        'Authorization': 'Bearer {}'.format(spotify_token.get('access_token'))
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        print("Spotify token is valid.")
    else:
        print(f"Spotify token is invalid. Error: {response.json()}")


def get_spotify_client() -> spotipy.Spotify:
    """
    Get or create a cached Spotify client instance (thread-safe singleton).
    
    This function creates the Spotify client once and reuses it for all
    subsequent calls. Uses a lock to ensure thread safety.
    Token is validated only on first call to avoid duplicate log messages.
    
    Returns:
        A configured Spotipy client instance
    """
    global _spotify_client, _token_validated

    # Fast path: return cached client without acquiring lock
    if _spotify_client is not None:
        return _spotify_client

    # Thread-safe initialization
    with _lock:
        # Double-check after acquiring lock (another thread may have initialized)
        if _spotify_client is not None:
            return _spotify_client

        scope = 'playlist-read-collaborative playlist-modify-public playlist-modify-private'
        client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        # Validate token only once
        if not _token_validated:
            spotify_token = client.auth_manager.get_access_token()
            check_spotify_token(spotify_token)
            _token_validated = True

        _spotify_client = client

    return _spotify_client


# Backward compatibility alias (deprecated)
def get_spotify_access_token() -> spotipy.Spotify:
    """Deprecated: Use get_spotify_client() instead."""
    return get_spotify_client()
