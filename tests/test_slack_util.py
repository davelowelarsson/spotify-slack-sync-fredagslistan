import pytest
from unittest.mock import MagicMock, patch
from utils.slack_util import check_slack_token, get_recent_slack_tracks, extract_spotify_track_ids, is_message_within_window
from freezegun import freeze_time
import os


# Unit tests for is_message_within_window (rolling window)
class TestIsMessageWithinWindow:
    """Unit tests for the is_message_within_window function."""

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_today_is_included(self):
        """Message from today should be included."""
        message = {'ts': '1641556800.123456'}  # Jan 7
        assert is_message_within_window(message) is True

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_yesterday_is_included(self):
        """Message from yesterday should be included."""
        message = {'ts': '1641470400.123456'}  # Jan 6
        assert is_message_within_window(message) is True

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_5_days_ago_is_included(self):
        """Message from 5 days ago should be included."""
        message = {'ts': '1641124800.123456'}  # Jan 2 (5 days ago)
        assert is_message_within_window(message) is True

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_6_days_ago_is_included(self):
        """Message from 6 days ago should be included (boundary)."""
        message = {
            'ts': '1641038400.123456'}  # Jan 1 00:00:00 UTC (6 days ago)
        assert is_message_within_window(message) is True

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_6_days_ago_at_midnight_is_included(self):
        """Message at exactly midnight 6 days ago should be included (exact boundary)."""
        # Jan 1, 2022 00:00:00 UTC = 1640995200
        message = {'ts': '1640995200.000000'}
        assert is_message_within_window(message) is True

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_7_days_ago_is_excluded(self):
        """Message from 7 days ago should be excluded (last Friday)."""
        message = {'ts': '1640952000.123456'}  # Dec 31 (7 days ago)
        assert is_message_within_window(message) is False

    @freeze_time("2022-01-07")  # Friday
    def test_message_from_7_days_ago_at_2359_is_excluded(self):
        """Message at 23:59 on day 7 (just before midnight) should be excluded."""
        # Dec 31, 2021 23:59:59 UTC = 1640995199
        message = {'ts': '1640995199.000000'}
        assert is_message_within_window(message) is False

    @freeze_time("2022-01-07")  # Friday
    def test_custom_days_back_parameter(self):
        """Test custom days_back parameter."""
        message = {'ts': '1641124800.123456'}  # Jan 2 (5 days ago)
        # With days_back=4, Jan 2 should be excluded
        assert is_message_within_window(message, days_back=4) is False
        # With days_back=5, Jan 2 should be included
        assert is_message_within_window(message, days_back=5) is True


# Unit tests for extract_spotify_track_ids helper function
class TestExtractSpotifyTrackIds:
    """Unit tests for the extract_spotify_track_ids helper function."""

    def test_single_track_standard_url(self):
        text = "Check out: https://open.spotify.com/track/32M0hVHxSzweqkrIJOxJqN"
        result = extract_spotify_track_ids(text)
        assert result == ['32M0hVHxSzweqkrIJOxJqN']

    def test_multiple_tracks_in_text(self):
        text = "Song 1: https://open.spotify.com/track/track1 and Song 2: https://open.spotify.com/track/track2"
        result = extract_spotify_track_ids(text)
        assert result == ['track1', 'track2']

    def test_track_with_country_code(self):
        text = "Italian track: https://open.spotify.com/track/IT/32M0hVHxSzweqkrIJOxJqN"
        result = extract_spotify_track_ids(text)
        assert result == ['32M0hVHxSzweqkrIJOxJqN']

    def test_track_with_query_params(self):
        text = "Song: https://open.spotify.com/track/track123?si=abc123&utm_source=copy"
        result = extract_spotify_track_ids(text)
        assert result == ['track123']

    def test_track_with_country_code_and_query_params(self):
        text = "Song: https://open.spotify.com/track/SE/track456?si=xyz789"
        result = extract_spotify_track_ids(text)
        assert result == ['track456']

    def test_no_spotify_links(self):
        text = "Just a regular message without any links"
        result = extract_spotify_track_ids(text)
        assert result == []

    def test_empty_string(self):
        result = extract_spotify_track_ids("")
        assert result == []

    def test_non_track_spotify_link(self):
        text = "Playlist: https://open.spotify.com/playlist/abc123"
        result = extract_spotify_track_ids(text)
        assert result == []

    def test_mixed_content(self):
        text = """Here's my playlist for today:
        https://open.spotify.com/track/track1
        Check also: https://open.spotify.com/track/SE/track2?si=abc
        And this album: https://open.spotify.com/album/album123
        Finally: https://open.spotify.com/track/track3"""
        result = extract_spotify_track_ids(text)
        assert result == ['track1', 'track2', 'track3']


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_check_slack_token(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {"ok": True}
    mock_client.auth_test.return_value = mock_response

    # Act
    check_slack_token()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.auth_test.assert_called_once()
    assert mock_response["ok"]

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_check_slack_token_invalid(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {"ok": False}
    mock_client.auth_test.return_value = mock_response

    # Act
    check_slack_token()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.auth_test.assert_called_once()
    assert not mock_response["ok"]

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
# Replace with the date corresponding to the 'ts' in your mock_response
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1'
            },
            {
                'ts': '1641234567.123457',
                'text': 'Another song: https://open.spotify.com/track/track2'
            },
            {
                'ts': '1641234567.123458',
                'text': 'Not a Spotify link'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.conversations_history.assert_called_once_with(
        channel='CAB3JFSQN')
    assert len(result) == 2
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}
    assert result[1] == {'track_id': 'track2',
                         'timestamp': '1641234567.123457'}

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks_multiple_links_in_one_message(mock_WebClient):
    """Test that multiple Spotify links in a single message are all extracted."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out these songs: https://open.spotify.com/track/track1 and https://open.spotify.com/track/track2 and also https://open.spotify.com/track/track3'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 3
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}
    assert result[1] == {'track_id': 'track2',
                         'timestamp': '1641234567.123456'}
    assert result[2] == {'track_id': 'track3',
                         'timestamp': '1641234567.123456'}


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks_with_country_code(mock_WebClient):
    """Test that Spotify links with country codes are correctly extracted."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Italian song: https://open.spotify.com/track/IT/track1'
            },
            {
                'ts': '1641234567.123457',
                'text': 'Swedish song: https://open.spotify.com/track/SE/track2'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 2
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}
    assert result[1] == {'track_id': 'track2',
                         'timestamp': '1641234567.123457'}


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks_with_query_params(mock_WebClient):
    """Test that Spotify links with query parameters are correctly extracted."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Song with params: https://open.spotify.com/track/track1?si=abc123&utm_source=copy-link'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 1
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks_includes_thread_messages(mock_WebClient):
    """Test that messages in threads are also checked for Spotify links."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client

    # Main channel messages - one has a thread (reply_count > 0)
    mock_history_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'reply_count': 2,
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123460',
                'text': 'Another song: https://open.spotify.com/track/track4'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_history_response

    # Thread replies
    mock_replies_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123457',
                'text': 'Reply with song: https://open.spotify.com/track/track2',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123458',
                'text': 'Another reply: https://open.spotify.com/track/track3',
                'thread_ts': '1641234567.123456'
            }
        ]
    }
    mock_client.conversations_replies.return_value = mock_replies_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    # Should have: track1 (main), track4 (main), track2 (thread), track3 (thread)
    # track1 is both in main and thread parent, should not be duplicated
    track_ids = [r['track_id'] for r in result]
    assert 'track1' in track_ids
    assert 'track2' in track_ids
    assert 'track3' in track_ids
    assert 'track4' in track_ids
    # Verify conversations_replies was called for the threaded message
    mock_client.conversations_replies.assert_called()


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_recent_slack_tracks_no_duplicate_from_threads(mock_WebClient):
    """Test that the same track from thread parent and main message is not duplicated."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client

    mock_history_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'reply_count': 1,
                'thread_ts': '1641234567.123456'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_history_response

    # Thread includes parent message plus reply with same track
    mock_replies_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123457',
                'text': 'I love this too: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            }
        ]
    }
    mock_client.conversations_replies.return_value = mock_replies_response

    # Act
    result = get_recent_slack_tracks()

    # Assert - track1 should appear only once (deduplication by track_id)
    track_ids = [r['track_id'] for r in result]
    # The function deduplicates track_ids; verify only one occurrence of 'track1'
    assert track_ids.count('track1') == 1


# Tests for rolling window (messages from last N days)
@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-07")  # Friday
def test_get_slack_urls_includes_messages_from_past_days(mock_WebClient):
    """Test that messages from the past 6 days are included (not just today)."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client

    # Messages from different days:
    # Jan 7 (today/Friday): 1641556800
    # Jan 6 (Thursday): 1641470400
    # Jan 5 (Wednesday): 1641384000
    # Jan 4 (Tuesday): 1641297600
    # Jan 3 (Monday): 1641211200
    # Jan 2 (Sunday): 1641124800
    # Jan 1 (Saturday - 6 days ago): 1641038400
    # Dec 31 (7 days ago - should be excluded): 1640952000
    mock_response = {
        'messages': [
            {
                'ts': '1641556800.123456',  # Jan 7 (today)
                'text': 'Friday song: https://open.spotify.com/track/fridayTrack123'
            },
            {
                'ts': '1641470400.123456',  # Jan 6 (1 day ago)
                'text': 'Thursday song: https://open.spotify.com/track/thursdayTrack456'
            },
            {
                'ts': '1641384000.123456',  # Jan 5 (2 days ago)
                'text': 'Wednesday song: https://open.spotify.com/track/wednesdayTrack789'
            },
            {
                'ts': '1641124800.123456',  # Jan 2 (5 days ago)
                'text': 'Sunday song: https://open.spotify.com/track/sundayTrackABC'
            },
            {
                # Dec 31 (7 days ago - should be excluded)
                'ts': '1640952000.123456',
                'text': 'Old song: https://open.spotify.com/track/oldTrackXYZ'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert - should include tracks from last 6 days but not 7 days ago
    track_ids = [r['track_id'] for r in result]
    assert 'fridayTrack123' in track_ids
    assert 'thursdayTrack456' in track_ids
    assert 'wednesdayTrack789' in track_ids
    assert 'sundayTrackABC' in track_ids
    assert 'oldTrackXYZ' not in track_ids  # 7 days ago should be excluded


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-07")  # Friday
def test_get_slack_urls_excludes_last_friday(mock_WebClient):
    """Test that messages from exactly 7 days ago (last Friday) are excluded."""
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client

    # Dec 31 was a Friday (7 days before Jan 7)
    mock_response = {
        'messages': [
            {
                'ts': '1641556800.123456',  # Jan 7 (today/Friday)
                'text': 'This Friday: https://open.spotify.com/track/thisFridayTrack'
            },
            {
                'ts': '1640952000.123456',  # Dec 31 (last Friday - 7 days ago)
                'text': 'Last Friday: https://open.spotify.com/track/lastFridayTrack'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_recent_slack_tracks()

    # Assert
    track_ids = [r['track_id'] for r in result]
    assert 'thisFridayTrack' in track_ids
    assert 'lastFridayTrack' not in track_ids  # Last Friday should be excluded
