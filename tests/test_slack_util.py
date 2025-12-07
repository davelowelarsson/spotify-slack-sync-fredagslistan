import pytest
from unittest.mock import MagicMock, patch
from utils.slack_util import (
    check_slack_token,
    get_recent_slack_tracks,
    extract_spotify_track_ids,
    is_message_within_window,
    get_random_topic_message,
    update_channel_topic,
    post_playlist_announcement,
    announce_new_playlist,
    get_user_display_name,
    get_year_contributors,
    TOPIC_MESSAGES,
    _user_cache,
)
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
                'user': 'U123ABC',
                'text': 'Check out this song: https://open.spotify.com/track/track1'
            },
            {
                'ts': '1641234567.123457',
                'user': 'U456DEF',
                'text': 'Another song: https://open.spotify.com/track/track2'
            },
            {
                'ts': '1641234567.123458',
                'user': 'U789GHI',
                'text': 'Not a Spotify link'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    # Mock users_info to return display names
    mock_client.users_info.side_effect = lambda user: {
        'ok': True,
        'user': {'profile': {'display_name': f'User_{user}'}}
    }

    # Act
    result = get_recent_slack_tracks()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.conversations_history.assert_called_once_with(
        channel='CAB3JFSQN')
    assert len(result) == 2
    # Check track_id and timestamp
    assert result[0]['track_id'] == 'track1'
    assert result[0]['timestamp'] == '1641234567.123456'
    assert result[0]['user_id'] == 'U123ABC'
    assert 'user_name' in result[0]
    assert result[1]['track_id'] == 'track2'
    assert result[1]['timestamp'] == '1641234567.123457'
    assert result[1]['user_id'] == 'U456DEF'

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
                'user': 'U123ABC',
                'text': 'Check out these songs: https://open.spotify.com/track/track1 and https://open.spotify.com/track/track2 and also https://open.spotify.com/track/track3'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 3
    assert result[0]['track_id'] == 'track1'
    assert result[0]['timestamp'] == '1641234567.123456'
    assert result[1]['track_id'] == 'track2'
    assert result[2]['track_id'] == 'track3'


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
                'user': 'U123ABC',
                'text': 'Italian song: https://open.spotify.com/track/IT/track1'
            },
            {
                'ts': '1641234567.123457',
                'user': 'U456DEF',
                'text': 'Swedish song: https://open.spotify.com/track/SE/track2'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 2
    assert result[0]['track_id'] == 'track1'
    assert result[0]['timestamp'] == '1641234567.123456'
    assert result[1]['track_id'] == 'track2'
    assert result[1]['timestamp'] == '1641234567.123457'


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
                'user': 'U123ABC',
                'text': 'Song with params: https://open.spotify.com/track/track1?si=abc123&utm_source=copy-link'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

    # Act
    result = get_recent_slack_tracks()

    # Assert
    assert len(result) == 1
    assert result[0]['track_id'] == 'track1'
    assert result[0]['timestamp'] == '1641234567.123456'


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
                'user': 'U123ABC',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'reply_count': 2,
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123460',
                'user': 'U456DEF',
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
                'user': 'U123ABC',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123457',
                'user': 'U789GHI',
                'text': 'Reply with song: https://open.spotify.com/track/track2',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123458',
                'user': 'UABCDEF',
                'text': 'Another reply: https://open.spotify.com/track/track3',
                'thread_ts': '1641234567.123456'
            }
        ]
    }
    mock_client.conversations_replies.return_value = mock_replies_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

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
                'user': 'U123ABC',
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
                'user': 'U123ABC',
                'text': 'Check out this song: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            },
            {
                'ts': '1641234567.123457',
                'user': 'U456DEF',
                'text': 'I love this too: https://open.spotify.com/track/track1',
                'thread_ts': '1641234567.123456'
            }
        ]
    }
    mock_client.conversations_replies.return_value = mock_replies_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

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
                'user': 'U123ABC',
                'text': 'Friday song: https://open.spotify.com/track/fridayTrack123'
            },
            {
                'ts': '1641470400.123456',  # Jan 6 (1 day ago)
                'user': 'U123ABC',
                'text': 'Thursday song: https://open.spotify.com/track/thursdayTrack456'
            },
            {
                'ts': '1641384000.123456',  # Jan 5 (2 days ago)
                'user': 'U123ABC',
                'text': 'Wednesday song: https://open.spotify.com/track/wednesdayTrack789'
            },
            {
                'ts': '1641124800.123456',  # Jan 2 (5 days ago)
                'user': 'U123ABC',
                'text': 'Sunday song: https://open.spotify.com/track/sundayTrackABC'
            },
            {
                # Dec 31 (7 days ago - should be excluded)
                'ts': '1640952000.123456',
                'user': 'U123ABC',
                'text': 'Old song: https://open.spotify.com/track/oldTrackXYZ'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

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
                'user': 'U123ABC',
                'text': 'This Friday: https://open.spotify.com/track/thisFridayTrack'
            },
            {
                'ts': '1640952000.123456',  # Dec 31 (last Friday - 7 days ago)
                'user': 'U456DEF',
                'text': 'Last Friday: https://open.spotify.com/track/lastFridayTrack'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response
    mock_client.users_info.return_value = {
        'ok': True, 'user': {'profile': {'display_name': 'TestUser'}}}

    # Act
    result = get_recent_slack_tracks()

    # Assert
    track_ids = [r['track_id'] for r in result]
    assert 'thisFridayTrack' in track_ids
    assert 'lastFridayTrack' not in track_ids  # Last Friday should be excluded


# Tests for new Slack messaging functions
class TestTopicMessages:
    """Tests for topic message generation."""

    def test_get_random_topic_message_contains_url(self):
        """Test that generated topic contains the URL."""
        url = "https://open.spotify.com/playlist/test123"
        topic = get_random_topic_message(2025, url)
        assert url in topic

    def test_get_random_topic_message_contains_year(self):
        """Test that generated topic may contain the year."""
        url = "https://open.spotify.com/playlist/test123"
        # Run multiple times to check various messages
        found_with_year = False
        for _ in range(100):
            topic = get_random_topic_message(2025, url)
            if "2025" in topic:
                found_with_year = True
                break
        # At least some messages should contain the year
        assert found_with_year or url in topic

    def test_topic_messages_list_not_empty(self):
        """Test that we have topic messages defined."""
        assert len(TOPIC_MESSAGES) > 0

    def test_all_topic_templates_are_valid(self):
        """Test that all topic message templates can be formatted."""
        url = "https://open.spotify.com/playlist/test"
        year = 2025
        for template in TOPIC_MESSAGES:
            # Should not raise an error
            result = template.format(year=year, url=url)
            assert url in result


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_update_channel_topic_success(mock_WebClient):
    """Test successfully updating channel topic."""
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.conversations_setTopic.return_value = {"ok": True}

    result = update_channel_topic("C123456", "New topic")

    assert result is True
    mock_client.conversations_setTopic.assert_called_once_with(
        channel="C123456",
        topic="New topic"
    )


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_update_channel_topic_failure(mock_WebClient):
    """Test handling failure when updating channel topic."""
    from slack_sdk.errors import SlackApiError

    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.conversations_setTopic.side_effect = SlackApiError(
        message="channel_not_found",
        response={"ok": False, "error": "channel_not_found"}
    )

    result = update_channel_topic("C123456", "New topic")

    assert result is False


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_post_playlist_announcement_success(mock_WebClient):
    """Test successfully posting a playlist announcement."""
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.chat_postMessage.return_value = {"ok": True}

    result = post_playlist_announcement(
        channel_id="C123456",
        playlist_name="Fredagslistan ! 2025 !",
        playlist_url="https://open.spotify.com/playlist/test123",
        year=2025
    )

    assert result is True
    mock_client.chat_postMessage.assert_called_once()
    call_kwargs = mock_client.chat_postMessage.call_args[1]
    assert call_kwargs['channel'] == "C123456"
    assert 'blocks' in call_kwargs
    assert len(call_kwargs['blocks']) > 0


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_post_playlist_announcement_failure(mock_WebClient):
    """Test handling failure when posting announcement."""
    from slack_sdk.errors import SlackApiError

    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.chat_postMessage.side_effect = SlackApiError(
        message="not_in_channel",
        response={"ok": False, "error": "not_in_channel"}
    )

    result = post_playlist_announcement(
        channel_id="C123456",
        playlist_name="Test Playlist",
        playlist_url="https://open.spotify.com/playlist/test",
        year=2025
    )

    assert result is False


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_announce_new_playlist_both_succeed(mock_WebClient):
    """Test announcing playlist when both message and topic update succeed."""
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_client.conversations_setTopic.return_value = {"ok": True}

    playlist = {
        'id': 'playlist123',
        'name': 'Fredagslistan ! 2025 !',
        'url': 'https://open.spotify.com/playlist/playlist123',
        'description': 'UR pepp 2025'
    }

    message_posted, topic_updated = announce_new_playlist(
        channel_id="C123456",
        playlist=playlist,
        year=2025
    )

    assert message_posted is True
    assert topic_updated is True


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_announce_new_playlist_message_fails(mock_WebClient):
    """Test announcing playlist when message fails but topic succeeds."""
    from slack_sdk.errors import SlackApiError

    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.chat_postMessage.side_effect = SlackApiError(
        message="error",
        response={"ok": False, "error": "some_error"}
    )
    mock_client.conversations_setTopic.return_value = {"ok": True}

    playlist = {
        'id': 'playlist123',
        'name': 'Fredagslistan ! 2025 !',
        'url': 'https://open.spotify.com/playlist/playlist123',
        'description': 'UR pepp 2025'
    }

    message_posted, topic_updated = announce_new_playlist(
        channel_id="C123456",
        playlist=playlist,
        year=2025
    )

    assert message_posted is False
    assert topic_updated is True


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_post_playlist_announcement_contains_button(mock_WebClient):
    """Test that the announcement contains an action button."""
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_client.chat_postMessage.return_value = {"ok": True}

    post_playlist_announcement(
        channel_id="C123456",
        playlist_name="Fredagslistan ! 2025 !",
        playlist_url="https://open.spotify.com/playlist/test123",
        year=2025
    )

    call_kwargs = mock_client.chat_postMessage.call_args[1]
    blocks = call_kwargs['blocks']

    # Find the actions block with the button
    actions_block = None
    for block in blocks:
        if block.get('type') == 'actions':
            actions_block = block
            break

    assert actions_block is not None
    assert len(actions_block['elements']) > 0
    button = actions_block['elements'][0]
    assert button['type'] == 'button'
    assert button['url'] == 'https://open.spotify.com/playlist/test123'


# Tests for get_user_display_name
class TestGetUserDisplayName:
    """Tests for the get_user_display_name function."""

    def setup_method(self):
        """Clear user cache before each test."""
        _user_cache.clear()

    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    def test_returns_display_name_when_available(self):
        """Should return display_name when available."""
        mock_client = MagicMock()
        mock_client.users_info.return_value = {
            'ok': True,
            'user': {
                'name': 'johndoe',
                'profile': {
                    'display_name': 'John Doe',
                    'real_name': 'John D'
                }
            }
        }

        result = get_user_display_name(mock_client, 'U12345')
        assert result == 'John Doe'

    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    def test_falls_back_to_real_name(self):
        """Should fall back to real_name when display_name is empty."""
        mock_client = MagicMock()
        mock_client.users_info.return_value = {
            'ok': True,
            'user': {
                'name': 'johndoe',
                'profile': {
                    'display_name': '',
                    'real_name': 'John Doe Real'
                }
            }
        }

        result = get_user_display_name(mock_client, 'U12345')
        assert result == 'John Doe Real'

    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    def test_uses_cache_on_subsequent_calls(self):
        """Should cache user lookups to avoid repeated API calls."""
        mock_client = MagicMock()
        mock_client.users_info.return_value = {
            'ok': True,
            'user': {
                'name': 'johndoe',
                'profile': {'display_name': 'Cached Name'}
            }
        }

        # First call
        result1 = get_user_display_name(mock_client, 'U12345')
        # Second call
        result2 = get_user_display_name(mock_client, 'U12345')

        assert result1 == 'Cached Name'
        assert result2 == 'Cached Name'
        # API should only be called once due to caching
        assert mock_client.users_info.call_count == 1

    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    def test_falls_back_to_user_id_on_error(self):
        """Should fall back to user_id when API call fails."""
        from slack_sdk.errors import SlackApiError

        mock_client = MagicMock()
        mock_client.users_info.side_effect = SlackApiError(
            message="user_not_found",
            response={'error': 'user_not_found'}
        )

        result = get_user_display_name(mock_client, 'U99999')
        assert result == 'U99999'


# Tests for get_year_contributors
class TestGetYearContributors:
    """Tests for the get_year_contributors function."""

    def setup_method(self):
        """Clear user cache before each test."""
        _user_cache.clear()

    @freeze_time("2024-12-31")
    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    @patch('utils.slack_util.WebClient')
    def test_returns_top_contributors(self, mock_WebClient):
        """Should return top contributors sorted by track count."""
        mock_client = MagicMock()
        mock_WebClient.return_value = mock_client
        mock_client.auth_test.return_value = {"ok": True}

        # Mock conversation history with messages containing Spotify links
        mock_client.conversations_history.return_value = {
            'messages': [
                {'user': 'U001', 'text': 'https://open.spotify.com/track/abc123',
                    'ts': '1704067200.0'},
                {'user': 'U001', 'text': 'https://open.spotify.com/track/def456',
                    'ts': '1704153600.0'},
                {'user': 'U002', 'text': 'https://open.spotify.com/track/ghi789',
                    'ts': '1704240000.0'},
            ],
            'response_metadata': {}
        }

        # Mock user info
        mock_client.users_info.side_effect = [
            {'ok': True, 'user': {'profile': {'display_name': 'Alice'}}},
            {'ok': True, 'user': {'profile': {'display_name': 'Bob'}}},
        ]

        result = get_year_contributors('C123', 2024, limit=5)

        assert len(result) == 2
        assert result[0]['user_name'] == 'Alice'
        assert result[0]['track_count'] == 2
        assert result[1]['user_name'] == 'Bob'
        assert result[1]['track_count'] == 1

    @freeze_time("2024-12-31")
    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    @patch('utils.slack_util.WebClient')
    def test_respects_limit_parameter(self, mock_WebClient):
        """Should respect the limit parameter."""
        mock_client = MagicMock()
        mock_WebClient.return_value = mock_client
        mock_client.auth_test.return_value = {"ok": True}

        # Create messages from 5 different users
        mock_client.conversations_history.return_value = {
            'messages': [
                {'user': f'U00{i}', 'text': f'https://open.spotify.com/track/track{i}',
                    'ts': f'{1704067200 + i}.0'}
                for i in range(1, 6)
            ],
            'response_metadata': {}
        }

        # Mock user info
        mock_client.users_info.side_effect = [
            {'ok': True, 'user': {'profile': {'display_name': f'User{i}'}}}
            for i in range(1, 4)  # Only 3 calls due to limit
        ]

        result = get_year_contributors('C123', 2024, limit=3)

        assert len(result) == 3

    @freeze_time("2024-12-31")
    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    @patch('utils.slack_util.WebClient')
    def test_counts_multiple_tracks_in_one_message(self, mock_WebClient):
        """Should count multiple tracks shared in a single message."""
        mock_client = MagicMock()
        mock_WebClient.return_value = mock_client
        mock_client.auth_test.return_value = {"ok": True}

        # One message with multiple tracks
        mock_client.conversations_history.return_value = {
            'messages': [
                {
                    'user': 'U001',
                    'text': 'Check these out: https://open.spotify.com/track/abc https://open.spotify.com/track/def https://open.spotify.com/track/ghi',
                    'ts': '1704067200.0'
                },
            ],
            'response_metadata': {}
        }

        mock_client.users_info.return_value = {
            'ok': True,
            'user': {'profile': {'display_name': 'MultiTracker'}}
        }

        result = get_year_contributors('C123', 2024, limit=5)

        assert len(result) == 1
        assert result[0]['user_name'] == 'MultiTracker'
        assert result[0]['track_count'] == 3

    @freeze_time("2024-12-31")
    @patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
    @patch('utils.slack_util.WebClient')
    def test_returns_empty_list_when_no_tracks(self, mock_WebClient):
        """Should return empty list when no tracks are found."""
        mock_client = MagicMock()
        mock_WebClient.return_value = mock_client
        mock_client.auth_test.return_value = {"ok": True}

        mock_client.conversations_history.return_value = {
            'messages': [
                {'user': 'U001', 'text': 'Just a regular message', 'ts': '1704067200.0'},
            ],
            'response_metadata': {}
        }

        result = get_year_contributors('C123', 2024, limit=5)

        assert result == []
