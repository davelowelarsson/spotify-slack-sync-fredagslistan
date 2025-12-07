# Agent Guidelines for spotify-slack-sync-fredagslistan

## Project Overview

This project syncs Spotify tracks shared in a Slack channel (#fredagslistan) to a Spotify playlist. It runs on a schedule every Friday between 08:00-18:00 via GitHub Actions.

### Core Workflow

1. Fetch messages from Slack channel from the last 6 days (including threads)
2. Extract Spotify track IDs from messages
3. Compare with tracks added to Spotify playlist in the last 6 days
4. Add new tracks to the playlist (preserving chronological order)

### Rolling Window (6 Days)

Both Slack messages AND Spotify playlist tracks use a 6-day rolling window:

- **Slack**: Captures songs shared earlier in the week leading up to Friday
- **Spotify**: Only checks recent additions, allowing songs to "come back"
- **Why 6 days?**: Skips last Friday's songs (7+ days ago) to avoid duplicates within the same week
- **Song comeback**: If a song was added 2 months ago but is shared again, it gets re-added!

## Tech Stack

- **Python 3.8+** - Main programming language
- **spotipy** - Spotify Web API wrapper
- **slack_sdk** - Slack Web API client
- **pytest** - Testing framework
- **freezegun** - Time mocking for tests
- **python-dotenv** - Environment variable management

## Project Structure

```text
├── main.py                      # Entry point - orchestrates sync workflow
├── utils/
│   ├── slack_util.py           # Slack API interactions
│   ├── spotify_util.py         # Spotify API interactions
│   ├── spotify_access_token.py # Spotify OAuth handling
│   └── texts.py                # Dynamic text templates for announcements
├── tests/
│   ├── test_slack_util.py      # Slack utility tests (103 tests total)
│   ├── test_spotify_util.py    # Spotify utility tests
│   └── test_texts.py           # Text template tests
├── .github/workflows/
│   └── main.yml                # GitHub Actions workflow
└── requirements.txt            # Python dependencies
```

## Coding Standards

### Python Best Practices

- Use type hints for function signatures
- Follow PEP 8 style guidelines
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Document complex logic with comments

### Testing Standards

- Use pytest with fixtures for test setup
- Mock external API calls (Slack, Spotify)
- Use `freezegun` to mock dates/times for consistent tests
- Follow Arrange-Act-Assert pattern
- Test edge cases (empty lists, malformed URLs, etc.)

### Test Pattern Example

```python
@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_function_name(mock_WebClient):
    # Arrange - set up mocks and test data
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client

    # Act - call the function under test
    result = function_under_test()

    # Assert - verify expected behavior
    assert result == expected_value
```

## API Integration Guidelines

### Slack SDK (slack_sdk)

- Use `WebClient` for API calls
- Key methods:
  - `conversations_history()` - Get channel messages
  - `conversations_replies()` - Get thread messages
  - `users_info()` - Get user display name (requires `users:read` scope)
  - `chat_postMessage()` - Post announcements with Block Kit
  - `conversations_setTopic()` - Update channel topic
- Messages contain `ts` (timestamp) and `thread_ts` (if part of a thread)
- Check `reply_count` to identify messages with threads
- User cache: `_user_cache` dict to minimize API calls for user lookups

### Spotipy (Spotify Python SDK)

- Use `playlist_add_items()` for adding tracks (not deprecated `user_playlist_add_tracks`)
- Track IDs can be extracted from URLs: `open.spotify.com/track/{track_id}`
- Handle country codes in URLs: `open.spotify.com/track/XX/{track_id}`
- Use pagination with `sp.next()` for large playlists

### Spotify URL Patterns

```python
# Standard format
https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN

# With country code
https://open.spotify.com/track/IT/32M0hVHxSzweqkrIJOxJqN

# With query params
https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN?si=abc123
```

### Regex for Track ID Extraction

```python
# Extract all track IDs from a message (handles multiple links)
import re
pattern = r'open\.spotify\.com/track/(?:[A-Z]{2}/)?([a-zA-Z0-9]+)'
track_ids = re.findall(pattern, message_text)
```

## Environment Variables

Required environment variables (store in `.env` locally, GitHub Secrets for CI):

```bash
SLACK_API_TOKEN=xoxb-...        # Slack Bot Token
SPOTIPY_CLIENT_ID=...           # Spotify App Client ID
SPOTIPY_CLIENT_SECRET=...       # Spotify App Client Secret
SPOTIPY_REDIRECT_URI=...        # OAuth redirect URI
```

## GitHub Actions Workflow

The workflow runs:

- On push to `main` branch
- Every 15 minutes on Fridays between 07:00-19:00 UTC

```yaml
on:
  schedule:
    - cron: '*/15 7-19 * * 5'  # Every 15 min, Fri 07:00-19:00 UTC
```

## Common Tasks

### Adding a New Feature

1. Write failing tests first (TDD)
2. Implement the feature
3. Run all tests to ensure no regressions
4. Update documentation if needed

### Running Tests

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_slack_util.py  # Run specific test file
pytest -k "test_name"     # Run tests matching pattern
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the sync
python main.py
```

## Key Implementation Details

### Multiple Spotify Links in One Message

Use `re.findall()` instead of `re.search()` to capture all track IDs when a message contains multiple Spotify links.

### Thread Message Handling

1. Check if message has `reply_count > 0` or `thread_ts`
2. Use `conversations_replies(channel, ts)` to fetch thread messages
3. Process thread messages same as regular messages
4. Preserve chronological order using message timestamps

### Duplicate Prevention

- Uses a 6-day rolling window for both Slack messages AND Spotify playlist
- Only prevents duplicates within the same 6-day window
- Songs added more than 6 days ago can be re-added (they "come back")
- Sort by timestamp to maintain order of addition

### Key Functions

**Slack Utilities (`slack_util.py`):**
- `is_message_within_window(message, days_back=6)` - Check if Slack message is within window
- `extract_spotify_track_ids(text)` - Extract all track IDs from a message (handles multiple links)
- `get_recent_slack_tracks(channel_id)` - Fetch all Spotify track IDs from recent Slack messages
- `get_user_display_name(client, user_id)` - Get user display name with caching
- `get_year_contributors(channel_id, year, limit)` - Get top contributors for a year (scans full year)
- `post_playlist_announcement()` - Post rich Block Kit announcement to Slack
- `announce_new_playlist()` - Announce new playlist and update channel topic

**Spotify Utilities (`spotify_util.py`):**
- `is_track_within_window(added_at, days_back=6)` - Check if Spotify track is within window
- `get_playlist(playlist_id, days_back)` - Get tracks from Spotify playlist within rolling window
- `find_playlist_by_year(year)` - Find existing playlist for a year
- `create_yearly_playlist(year)` - Create new playlist for a year
- `get_or_create_yearly_playlist(year)` - Get or create playlist (lazy creation)
- `get_playlist_stats(playlist_id)` - Get track count, top artists, top genres
- `get_previous_year_stats(year)` - Get stats from previous year's playlist

**Text Templates (`texts.py`):**
- `get_random_playlist_name(year)` - Generate random playlist name with emoji
- `get_random_topic_message(year, url)` - Generate channel topic message
- `get_random_announcement_header(year)` - Generate announcement header
- `format_top_genres(genres, limit)` - Format genres with emojis
- `format_top_artists(artists, limit)` - Format artists with numbers
- `format_top_contributors(contributors, limit)` - Format contributors with medals

**Main (`main.py`):**
- `compare_lists_and_remove_duplicates()` - Main orchestration function

### Timezone Handling

All datetime comparisons use UTC-aware datetimes:

- Slack timestamps are Unix timestamps - convert with `datetime.fromtimestamp(ts, tz=timezone.utc)`
- Spotify `added_at` is ISO 8601 format - parse with `datetime.fromisoformat(added_at.replace('Z', '+00:00'))`
- Use `datetime.now(tz=timezone.utc)` for current time comparisons

## Troubleshooting

### Spotify OAuth Issues

If OAuth token is invalid, you may need to re-authenticate manually:

1. Delete cached token
2. Run locally and paste redirect URL when prompted

### Rate Limiting

- Slack: ~1 request/second for most methods
- Spotify: Varies by endpoint, handle 429 responses with retry

### Testing Tips

- Use `freezegun` to freeze time for date-dependent tests
- Mock external APIs to avoid network calls in tests
- Use fixtures for common test setup

## Completed Features

- [x] Create new playlist automatically for each year (lazy creation)
- [x] Announce playlist in Slack with rich Block Kit formatting
- [x] Track statistics (track count, top artists, top genres)
- [x] Top 5 contributors leaderboard with medals (🥇🥈🥉)
- [x] Dynamic rotating text for all messages (10+ templates per category)
- [x] User attribution tracking (who shared what)
- [x] Pattern matching for old and new playlist naming conventions

## Future Improvements

- [ ] Handle albums and playlist links (not just tracks)
- [ ] Weekly digest of songs added
