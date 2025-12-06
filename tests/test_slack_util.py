import pytest
from unittest.mock import MagicMock, patch
from utils.slack_util import check_slack_token, get_todays_slack_urls, extract_spotify_track_ids
from freezegun import freeze_time
import os


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
def test_get_todays_slack_urls(mock_WebClient):
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
    result = get_todays_slack_urls()

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
def test_get_todays_slack_urls_multiple_links_in_one_message(mock_WebClient):
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
    result = get_todays_slack_urls()

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
def test_get_todays_slack_urls_with_country_code(mock_WebClient):
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
    result = get_todays_slack_urls()

    # Assert
    assert len(result) == 2
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}
    assert result[1] == {'track_id': 'track2',
                         'timestamp': '1641234567.123457'}


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_todays_slack_urls_with_query_params(mock_WebClient):
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
    result = get_todays_slack_urls()

    # Assert
    assert len(result) == 1
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
@freeze_time("2022-01-03")
def test_get_todays_slack_urls_includes_thread_messages(mock_WebClient):
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
    result = get_todays_slack_urls()

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
def test_get_todays_slack_urls_no_duplicate_from_threads(mock_WebClient):
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
    result = get_todays_slack_urls()

    # Assert - track1 should appear only once (deduplication by track_id)
    track_ids = [r['track_id'] for r in result]
    # The function deduplicates track_ids; verify only one occurrence of 'track1'
    assert track_ids.count('track1') == 1
