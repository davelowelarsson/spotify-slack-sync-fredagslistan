# this function will check a channel in a slack workspace for messages containing spotify links.
# it will return a list of spotiyfy links
# these links will be compared in a later function to a spotify playlist

# access slack channel
# get messages from slack channel
# check if message contains spotify link
# if yes, add to list
# return list

# import the slack client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from dotenv import load_dotenv
import re
from datetime import datetime

# Load .env file
load_dotenv()


def get_slack_client():
    # Get the Slack token from the environment variable
    slack_token = os.getenv("SLACK_API_TOKEN")

    # Instantiate a Web API client
    client = WebClient(token=slack_token)

    return slack_token, client

def check_slack_token():
    slack_token, client = get_slack_client()

    try:
        response = client.auth_test()
        if response["ok"]:
            print("Slack token is valid.")
        else:
            print("Slack token is invalid.")
    except SlackApiError as e:
        print(f"Error validating Slack token: {e.response['error']}")


def get_todays_slack_urls(channel_id="CAB3JFSQN"):
    slack_token, client = get_slack_client()

    check_slack_token()

    # get the messages from the #fredagslistan channel
    response = client.conversations_history(
        channel=channel_id
    )

    # retrieve the messages
    messages = response['messages']
    # print(messages)

    today_messages = [message for message in messages]

    # add id's from the spotify links to a list
    # for example 19udLuHd7CD8XxrOmUaXPn in https://open.spotify.com/track/19udLuHd7CD8XxrOmUaXPn
    spotify_links = []

    # print the messages
    for message in today_messages:
        if datetime.fromtimestamp(int(message['ts'].split(".")[0])).strftime('%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d'):
            # print(message["text"])
            # sometimes the track has acountry code like track/IT/19udLuHd7CD8XxrOmUaXPn in the url which I need to handle as well
            if "open.spotify.com/track" in message['text']:
                track_id = re.search(r'track/(\w+)', message['text'])
                # print(track_id)
                spotify_links.append(track_id.group(1))

    # # print length of list from slack
    # print('counted tracks added today in slack: ', len(spotify_links))

    # print(spotify_links)
    return spotify_links
