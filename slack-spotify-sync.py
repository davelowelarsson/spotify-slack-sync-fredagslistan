import datetime
import requests
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load .env file
load_dotenv()

# Instantiate a Web API client
slack_token = os.getenv("SLACK_API_TOKEN")
client = WebClient(token=slack_token)

# Spotify API token
spotify_token = os.getenv("SPOTIFY_API_TOKEN")

def check_slack_token():
    # TODO: Implement a function to check the Slack token.
    client = WebClient(token=slack_token)
    try:
        response = client.auth_test()
        if response["ok"]:
            print("Slack token is valid.")
        else:
            print("Slack token is invalid.")
    except SlackApiError as e:
        print(f"Error validating Slack token: {e.response['error']}")

def check_spotify_token():
    spotify_token = os.getenv("SPOTIFY_API_TOKEN")
    print(spotify_token)
    headers = {
        'Authorization': 'Bearer {}'.format(spotify_token)
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        print("Spotify token is valid.")
    else:
        print(f"Spotify token is invalid. Error: {response.json()}")


# def get_todays_slack_urls():
#     # TODO: Implement a function to fetch today's Spotify URLs from a specific Slack channel.

# def check_create_spotify_playlist():
#     # TODO: Implement a function to check if there's a playlist for today in Spotify.
#     # If there's no playlist, create a new one and return the ID.
#     # If there is a playlist, return the ID.

# def get_spotify_playlist_songs(playlist_id):
#     # TODO: Implement a function to fetch all songs from the given Spotify playlist.

# def compare_lists_and_remove_duplicates(slack_urls, spotify_songs):
#     # TODO: Implement a function to compare the Slack URLs with the Spotify song list.
#     # Remove any duplicates and return the remaining URLs.

# def add_songs_to_spotify_playlist(playlist_id, song_urls):
#     # TODO: Implement a function to add the remaining URLs to the Spotify playlist.

# def announce_playlist_in_slack(playlist_id):
#     # TODO: Implement a function to announce the playlist in Slack.
#     # Only do this once per day.
#     # Optionally, add a comment in the thread about the number of added songs each time it runs.

def main():
    check_slack_token()
    check_spotify_token()

    # slack_urls = get_todays_slack_urls()
    # if len(slack_urls) > 0:  # If there are new songs in Slack channel, continue.
    #     playlist_id = check_create_spotify_playlist()
    #     spotify_songs = get_spotify_playlist_songs(playlist_id)
    #     remaining_urls = compare_lists_and_remove_duplicates(slack_urls, spotify_songs)
    #     add_songs_to_spotify_playlist(playlist_id, remaining_urls)
    #     announce_playlist_in_slack(playlist_id)

if __name__ == "__main__":
    main()
