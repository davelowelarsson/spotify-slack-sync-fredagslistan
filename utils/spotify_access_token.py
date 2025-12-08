# Prepare spotify access
# export function to be used in main.py
#
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import requests

# Load environment variables from .env file (if exists)
# Spotipy reads SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI automatically
load_dotenv()

# Cached Spotify client instance (singleton pattern)
_spotify_client: spotipy.Spotify | None = None
_token_validated: bool = False


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


def get_spotify_access_token() -> spotipy.Spotify:
    """
    Get or create a cached Spotify client instance (singleton pattern).
    
    This function creates the Spotify client once and reuses it for all
    subsequent calls. The token is validated only on first call to avoid
    duplicate log messages.
    
    Returns:
        A configured Spotipy client instance
    """
    global _spotify_client, _token_validated

    # Return cached client if already created
    if _spotify_client is not None:
        return _spotify_client

    scope = 'playlist-read-collaborative playlist-modify-public playlist-modify-private'
    _spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # Validate token only once
    if not _token_validated:
        spotify_token = _spotify_client.auth_manager.get_access_token()
        check_spotify_token(spotify_token)
        _token_validated = True

    return _spotify_client
