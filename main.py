# start by getting spotify access-token
# import the file and runt the function
from utils.spotify_util import get_playlist, add_songs_to_spotify_playlist
from utils.slack_util import get_todays_slack_urls

from datetime import datetime


def compare_lists_and_remove_duplicates():
  songs_already_in_spotify = get_playlist()
  songs_added_in_slack = get_todays_slack_urls()

  # compare the two lists and create a new list without duplicates
  # if the song is in the spotify list it's not allowed to be added to the new list

  # create a new list
  songs_to_add = []

  # the lists have different formats which we need to ta into account
  # the slack list is a list of strings ex. ['32M0hVHxSzweqkrIJOxJqN', '2S2kBpCQQ3FXWK5terDA38']
  # the spotify list is a list of dictionaries ex. [{'name': 'The Less I Know The Better', 'url': 'https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN', 'track_id': '32M0hVHxSzweqkrIJOxJqN'}, {'name': 'The Less I Know The Better', 'url': 'https://open.spotify.com/track/2S2kBpCQQ3FXWK5terDA38', 'track_id': '2S2kBpCQQ3FXWK5terDA38'}]

  # count the length of both lists and the result should be the amount of songs in slack but not in spotify
  print('counted tracks added today in slack: ', len(songs_added_in_slack))
  print('counted tracks added today in spotify: ', len(songs_already_in_spotify))
  # print the difference between the two lists
  print('difference between slack and spotify lists: ', len(
      songs_added_in_slack) - len(songs_already_in_spotify))

  # Sort slack tracks by timestamp
  songs_added_in_slack_sorted = sorted(
      songs_added_in_slack, key=lambda x: x['timestamp'])


  # loop through the slack list
  for song in songs_added_in_slack_sorted:
    # check if the song is in the spotify list
    # if it's not in the list, add it to the new list
    if not any(song == s['track_id'] for s in songs_already_in_spotify):
        songs_to_add.append(song)

  # print the new list
  print('songs_to_add: ', len(songs_to_add))
  print(songs_to_add)
  return songs_to_add


def main():
  # get the songs to add to the spotify list
  songs_to_add = compare_lists_and_remove_duplicates()
  # add the songs to the spotify list
  add_songs_to_spotify_playlist(track_ids=songs_to_add)


main()
