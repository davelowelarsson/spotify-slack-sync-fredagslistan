# Prepare spotify access
# export function to be used in main.py
#
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import requests

from datetime import datetime

# try loading from .env file but use ENV variable if it exists
load_dotenv()


def check_spotify_token(spotify_token):
    spotify_token = spotify_token or os.getenv("SPOTIFY_API_TOKEN")

    print('Spotify token: ', spotify_token)
    print('Spotify token access_token: ', spotify_token.get('access_token'))

    headers = {
        'Authorization': 'Bearer {}'.format(spotify_token.get('access_token'))
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        print("Spotify token is valid.")
    else:
        print(f"Spotify token is invalid. Error: {response.json()}")


def get_spotify_access_token():
    scope = 'playlist-read-collaborative playlist-modify-public playlist-modify-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    print('Spotify token: ', sp.auth_manager.get_access_token())
    # ex.
    # spotify token:
    # {
    # 'access_token': 'BQDFkngd_TMgcHLRsIuaeX5QQvDm58_qk3V-nWm_0_J_-7GCXyhsXxVtsRXQSrsto3m-yAhsoLcHPXrCoBHn8_SYoA9EuhDagNqu1ke0MQIKud5ZTgQzWhpB3Xa8L55ebS1bU4aygQ-mFMeLd6xILTxlyve_iXT1v7p4RJX_L9NnbEv8TmmLUaTgcm36vPBPt_uFNps9Klq6ww',
    # 'token_type': 'Bearer',
    # 'expires_in': 3600,
    # 'refresh_token': 'AQB6X7hwVkU3co10ythQFkyv0WXRP8wQgUX9TgzavojwrGxBkdB7EDx6rsTvzibFKmHmuWAvrNoaMDnWOh-DHHEoOdtXksooh3Z2nnNL6p8BQmTUtRk3vmwUJ9ZH--uBa3w',
    # 'scope': 'playlist-read-collaborative playlist-modify-public',
    # 'expires_at': 1707489467
    # }

    spotify_token = sp.auth_manager.get_access_token()

    # print permissions for the token
    print(sp.me())

    check_spotify_token(spotify_token)

    return sp
