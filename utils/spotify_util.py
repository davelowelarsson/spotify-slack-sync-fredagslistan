from utils.spotify_access_token import get_spotify_access_token
from datetime import datetime


def get_playlist(playlist_id='1OdSuwMRWtpP0nVhLffEqe'):
    sp = get_spotify_access_token()

    # Print one single public playlist
    # https://open.spotify.com/playlist/45o1nZW7H9uruWYiR6pz9S?si=c734ae1351a84a9b

    playlist = sp.playlist(playlist_id)
    print(playlist['name'])
    print(playlist['description'])
    print(playlist['external_urls'])

    # Print length of tracks all tracks in the playlist
    print('counted tracks', len(playlist['tracks']['items']))
    print('  total tracks', playlist['tracks']['total'])

    print('Added today in Spotify: ')
    print(datetime.now().strftime('%Y-%m-%d'))

    # Save todays songs added in an array [name, url, track_id]
    todays_songs = []

    # print length of tracks added today
    for item in playlist['tracks']['items']:
        # print added date
        # print(item['added_at'])
        # if date is today print track name
        # example of todays date: 2024-02-02T08:18:14Z
        if item['added_at'].split('T')[0] == datetime.now().strftime('%Y-%m-%d'):
            todays_songs.append({
                'name': item['track']['name'],
                'url': item['track']['external_urls']['spotify'],
                'track_id': item['track']['id']
            })

    #  print length of tracks in spotify list
    print('counted tracks added today in spotify: ', len(todays_songs))

    # print all todays songs
    for song in todays_songs:
        print('Name: ', song['name'], 'URL: ',
              song['url'], 'Track ID: ', song['track_id'])

    return todays_songs


# Add tracks to playlist using track id
def add_songs_to_spotify_playlist(playlist_id='1OdSuwMRWtpP0nVhLffEqe', track_ids=[]):
    sp = get_spotify_access_token()

    print('######### Adding tracks to playlist: ###########')
    print(sp.me())
    print('sp access token: ', sp.auth_manager.get_access_token())

    # make sure the incoming tracks is a list with strings
    if not isinstance(track_ids, list):
        track_ids = [track_ids]

    if track_ids:
        print('Adding tracks: ', track_ids)
        sp.playlist_add_items(playlist_id, track_ids)
    else:
        print('No tracks to add to playlist.')
