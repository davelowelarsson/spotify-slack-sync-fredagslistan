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

3. Configure environment variables

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

4. Run the sync

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
- [x] Comprehensive test coverage
- [x] Create new playlist automatically for each year
- [x] Announce playlist in Slack (with Block Kit)
- [x] Update channel topic with playlist link
- [x] Track statistics (track count, top artists, genres)
- [x] Top contributors leaderboard with medals
- [x] Dynamic rotating text for all announcements
- [x] User attribution tracking (who shared what)
- [ ] Handle albums and playlist links (not just tracks)

## Spotify auth & token rotation

Spotify uses user-scoped OAuth (needed to modify playlists). Locally you do an
interactive OAuth once; CI (the Friday cron) authenticates non-interactively
from a **refresh token** stored as a GitHub Actions secret.

### First-time / local OAuth

Prerequisite: in the [Spotify app dashboard](https://developer.spotify.com/dashboard),
register the redirect URI `http://127.0.0.1:8888/callback` (Spotify requires an
explicit loopback IP — `localhost` is rejected) and set `SPOTIPY_REDIRECT_URI`
to the same value in your `.env`.

1. Run `uv run python main.py`
2. A browser window opens for Spotify authorization — click **Agree**
3. Spotify redirects to `http://127.0.0.1:8888/callback?code=…`, where spotipy's
   local server captures the code automatically (no copy-paste needed)

This writes a local `.cache` file (gitignored — never commit it).

### How CI authenticates

`get_spotify_client()` reads the `SPOTIPY_REFRESH_TOKEN` env var (set from a
GitHub Actions secret). When present, spotipy is seeded with that refresh token
**in memory** and mints a fresh access token on each run — no token file is
needed. When absent, it falls back to the local `.cache` / interactive flow
above (and, in CI with neither a token nor a `.cache`, fails fast with a clear
error rather than hanging on an interactive prompt).

> Migration note: a `.cache` file was historically committed to bootstrap CI.
> Once the `SPOTIPY_REFRESH_TOKEN` secret is set and a manual run is verified
> green, that committed cache is removed and purged from git history.

### Rotating the Spotify token

Do this to revoke a leaked/old token or on a schedule. It does **not** require
downtime — set the new secret before revoking the old app authorization.

1. **(Optional) new app credentials** — at
   [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard),
   either rotate the client secret of the existing app or create a new app.
   Update the `SPOTIPY_CLIENT_ID` / `SPOTIPY_CLIENT_SECRET` /
   `SPOTIPY_REDIRECT_URI` repo secrets to match.
2. **Mint a fresh refresh token locally**:

   ```sh
   rm -f .cache                 # discard any old cached token
   uv run python main.py        # do the interactive OAuth (writes a new .cache)
   # extract the refresh token from the new cache:
   uv run python -c "import json; print(json.load(open('.cache'))['refresh_token'])"
   ```

3. **Store it as a secret**:

   ```sh
   gh secret set SPOTIPY_REFRESH_TOKEN   # paste the value from step 2
   ```

4. **Verify** without waiting for Friday: trigger the workflow manually
   (`gh workflow run "Run main.py"` or the Actions tab → *Run workflow*) and
   confirm it prints "Spotify token is valid." and completes green.
5. **Revoke the old authorization** at
   [spotify.com/account/apps](https://www.spotify.com/account/apps/) once the
   new token is confirmed working. Any previously-committed token is now dead.

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
