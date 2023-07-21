import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys
import pprint
from dotenv import load_dotenv

# Load .env file
load_dotenv()

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = 'salta'

client_credentials_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
sp.trace = True
user = sp.user(username)
pprint.pprint(user)