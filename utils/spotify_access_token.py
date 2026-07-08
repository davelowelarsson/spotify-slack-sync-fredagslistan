# Prepare spotify access
# export function to be used in main.py
#
import os
import threading

import requests
import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file (if exists)
# Spotipy reads SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI automatically
load_dotenv()

# Cached Spotify client instance (singleton pattern)
_spotify_client: spotipy.Spotify | None = None
_token_validated: bool = False
_lock = threading.Lock()


def _build_auth_manager(scope: str) -> SpotifyOAuth:
    """Build the Spotify OAuth manager.

    In CI / headless runs, authenticate from a ``SPOTIPY_REFRESH_TOKEN`` secret
    held only in memory — nothing is read from or written to a committed token
    file. The token is seeded as already-expired so spotipy refreshes it on
    first use. Locally (no refresh token in the environment) we fall back to
    spotipy's default file-based cache (``.cache``) / interactive browser flow.
    """
    refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")
    if refresh_token:
        cache_handler = MemoryCacheHandler(
            token_info={
                "refresh_token": refresh_token,
                "access_token": "",
                "expires_at": 0,  # already expired -> forces a refresh
                "scope": scope,
                "token_type": "Bearer",
            }
        )
        return SpotifyOAuth(scope=scope, cache_handler=cache_handler, open_browser=False)

    # Local development: spotipy's default .cache file / interactive OAuth.
    return SpotifyOAuth(scope=scope)


def check_spotify_token(access_token: str) -> None:
    """Validate a Spotify access token against the /me endpoint and log the result."""
    headers = {"Authorization": f"Bearer {access_token}"}

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

        scope = "playlist-read-collaborative playlist-modify-public playlist-modify-private"
        client = spotipy.Spotify(auth_manager=_build_auth_manager(scope))

        # Validate token only once
        if not _token_validated and client.auth_manager is not None:
            access_token = client.auth_manager.get_access_token(as_dict=False)
            check_spotify_token(access_token)
            _token_validated = True

        _spotify_client = client

    return _spotify_client
