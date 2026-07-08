# Spotify-Slack Sync: Fredagslistan 🎵

Automatically syncs Spotify tracks shared in a Slack channel to a collaborative Spotify playlist. Perfect for team "Friday playlist" traditions!

## Features

- 🎵 **Multi-track extraction** - Captures all Spotify links from a single message
- 💬 **Thread support** - Fetches tracks from thread replies, not just main messages
- 📅 **6-day rolling window** - Captures the week's music leading up to Friday
- 🔄 **Smart deduplication** - Only adds new tracks within the rolling window
- ⏰ **Scheduled sync** - Runs automatically via GitHub Actions on Fridays
- 📆 **Yearly playlists** - Automatically creates a new playlist for each year
- 📢 **Slack announcements** - Posts a rich Block Kit message when a new playlist is created
- 📝 **Topic updates** - Updates the Slack channel topic with fun rotating messages
- 📊 **Year-end statistics** - Shows top artists, genres, and contributors from the previous year
- 🏆 **Top contributors** - Highlights the top 5 people who shared the most tracks
- 🎲 **Dynamic text** - Rotating fun messages for announcements, descriptions, and topics

## How It Works

1. Checks if a playlist exists for the current year (`Fredagslistan YYYY 🎵`)
2. If not, creates a new playlist and announces it in Slack (with Block Kit formatting)
3. Fetches stats from previous year's playlist (track count, top artists, genres)
4. Gets top 5 contributors from the previous year's Slack messages
5. Posts a rich announcement with all the stats and a link to the new playlist
6. Updates the Slack channel topic with the playlist link
7. Fetches messages from Slack channel (last 6 days, including threads)
8. Extracts Spotify track IDs from all messages
9. Compares with tracks already in the Spotify playlist
10. Adds new tracks to the playlist (preserving chronological order)

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python 3.13+ and dependencies)
- Slack Bot Token with these scopes:
  - `channels:history` - Read messages from channels
  - `chat:write` - Post announcement messages
  - `channels:manage` - Update channel topic
  - `users:read` - Get user display names for contributor stats
- Spotify Developer credentials with these scopes:
  - `playlist-read-collaborative`
  - `playlist-modify-public`
  - `playlist-modify-private`

### Installation

1. Clone the repository

   ```sh
   git clone https://github.com/davelowelarsson/spotify-slack-sync-fredagslistan.git
   cd spotify-slack-sync-fredagslistan
   ```

2. Install dependencies (uv creates the virtualenv and installs Python 3.13 if needed)

   ```sh
   uv sync
   ```

   > Using [mise](https://mise.jdx.dev/)? `mise install` provisions both Python and uv.

4. Configure environment variables

   ```sh
   cp .env.example .env
   # Edit .env with your credentials
   ```

   Required variables:

   ```bash
   SLACK_API_TOKEN=xoxb-...
   SPOTIPY_CLIENT_ID=...
   SPOTIPY_CLIENT_SECRET=...
   SPOTIPY_REDIRECT_URI=...
   ```

5. Run the sync

   ```sh
   uv run python main.py
   ```

## Usage

### Manual Run

```sh
uv run python main.py
```

### Automated (GitHub Actions)

The workflow runs every 15 minutes on Fridays between 07:00-19:00 UTC.


### Running Tests

```sh
uv run pytest                           # Run all tests
uv run pytest -v                        # Verbose output
uv run pytest tests/test_slack_util.py  # Specific test file
```

## Built With

- [![Python][Python-badge]][Python-url] - Programming language
- [![Spotify][Spotify-badge]][Spotify-url] - Music platform API (via spotipy)
- [![Slack][Slack-badge]][Slack-url] - Messaging platform API (via slack_sdk)

## Roadmap

- [x] Extract multiple Spotify links from single message
- [x] Support thread message extraction
- [x] 6-day rolling window for captures
- [x] Type hints throughout codebase
- [x] Comprehensive test coverage (109 tests)
- [x] Create new playlist automatically for each year
- [x] Announce playlist in Slack (with Block Kit)
- [x] Update channel topic with playlist link
- [x] Track statistics (track count, top artists, genres)
- [x] Top contributors leaderboard with medals
- [x] Dynamic rotating text for all announcements
- [x] User attribution tracking (who shared what)
- [ ] Handle albums and playlist links (not just tracks)

## Spotify OAuth

First-time setup requires manual OAuth authentication:

1. Run `uv run python main.py`
2. A browser window opens for Spotify authorization
3. After authorizing, copy the redirect URL
4. Paste in terminal when prompted:

   ```text
   Enter the URL you were redirected to:
   ```

   Example URL:

   ```text
   slack-spotify-sync://callback/?code=AQD0EADQNOg...
   ```

![OAuth Flow](images/2024-02-09-14-39-03.png)

## Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Write tests first (TDD approach)
4. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the Branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## License

Distributed under the MIT License.

## Acknowledgments

- Original concept by Jonas for the Friday playlist tradition
- [spotipy](https://spotipy.readthedocs.io/) - Spotify Web API wrapper
- [slack_sdk](https://slack.dev/python-slack-sdk/) - Slack API client

---

<!-- Badge definitions -->
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Spotify-badge]: https://img.shields.io/badge/Spotify-1DB954?style=for-the-badge&logo=spotify&logoColor=white
[Spotify-url]: https://developer.spotify.com/
[Slack-badge]: https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white
[Slack-url]: https://api.slack.com/
