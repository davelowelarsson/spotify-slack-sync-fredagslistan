# Shows a user's playlists (need to be authenticated via oauth)

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def show_tracks(results):
    for i, item in enumerate(results['items']):
        track = item['track']
        print(
            "   %d %32.32s %s" %
            (i, track['artists'][0]['name'], track['name']))


if __name__ == '__main__':
    scope = 'playlist-read-collaborative'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    playlists = sp.current_user_playlists()
    user_id = sp.me()['id']

    for playlist in playlists['items']:
        if playlist['id'] == '45o1nZW7H9uruWYiR6pz9S':
          print()
          print(playlist['name'])
          print(playlist['id'])
          print(playlist['owner']['id'])
          print(playlist['owner']['display_name'])
          print(playlist)
          print('  total tracks', playlist['tracks']['total'])

          results = sp.playlist(playlist['id'], fields="tracks,next")
          tracks = results['tracks']
          show_tracks(tracks)

          while tracks['next']:
              tracks = sp.next(tracks)
              show_tracks(tracks)