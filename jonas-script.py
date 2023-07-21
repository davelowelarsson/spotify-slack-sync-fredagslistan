import os
import time
import re
import requests
import slack
import base64
import pytz
from datetime import datetime

# Spotify API credentials
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_PLAYLIST_ID = ""

spotify_token = ""

# initialize the Slack API client
client = slack.WebClient(token=os.environ['BOT_TOKEN'])

# Add track to playlist
def add_track_to_playlist(track_uri, spotify_token):
    access_token = spotify_token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "uris": [track_uri]
    }
    response = requests.post(f"https://api.spotify.com/v1/playlists/{SPOTIFY_PLAYLIST_ID}/tracks", headers=headers, json=data)
    if response.status_code != 201:
        print(response.json())
        raise Exception("Could not add track to playlist")


def read_slack_messages():
    # get the messages from the #fredagslistan channel
    response = client.conversations_history(
        channel="CAB3JFSQN"
    )

    # retrieve the messages
    messages = response['messages']
    #print(messages)

    today_messages = [message for message in messages]

    # print the messages
    for message in today_messages:

        if datetime.fromtimestamp(int(message['ts'].split(".")[0])).strftime('%Y-%m-%d') == "2023-02-10":
            print(message["text"])
            if "open.spotify.com/track" in message['text']:




                track_id = re.search(r'track/(\w+)', message['text'])
                #print(track_id)

                if track_id.group(1):
                    track_uri = "spotify:track:" + track_id.group(1)

                    print(track_uri)
                    add_track_to_playlist(track_uri, spotify_token)

read_slack_messages()