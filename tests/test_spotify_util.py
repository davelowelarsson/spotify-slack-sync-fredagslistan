import pytest
from unittest.mock import MagicMock, patch
from utils.spotify_util import add_songs_to_spotify_playlist, get_playlist, is_track_within_window
from freezegun import freeze_time


# Unit tests for is_track_within_window
class TestIsTrackWithinWindow:
    """Unit tests for the is_track_within_window function."""

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_today_is_included(self):
        """Track added today should be included."""
        assert is_track_within_window('2022-01-07T12:00:00Z') is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_yesterday_is_included(self):
        """Track added yesterday should be included."""
        assert is_track_within_window('2022-01-06T12:00:00Z') is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_6_days_ago_is_included(self):
        """Track added 6 days ago should be included (boundary)."""
        assert is_track_within_window('2022-01-01T12:00:00Z') is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_7_days_ago_is_excluded(self):
        """Track added 7 days ago should be excluded."""
        assert is_track_within_window('2021-12-31T12:00:00Z') is False

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_2_months_ago_is_excluded(self):
        """Track added 2 months ago should be excluded (can come back!)."""
        assert is_track_within_window('2021-11-07T12:00:00Z') is False


@patch('utils.spotify_util.get_spotify_access_token')
def test_add_songs_to_spotify_playlist(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'
    track_ids = ['track1', 'track2', 'track3']

    # Act
    add_songs_to_spotify_playlist(playlist_id, track_ids)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist_add_items.assert_called_once_with(playlist_id, track_ids)


@patch('utils.spotify_util.get_spotify_access_token')
def test_add_songs_to_spotify_playlist_single_track(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'
    track_id = 'track1'

    # Act
    add_songs_to_spotify_playlist(playlist_id, track_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist_add_items.assert_called_once_with(playlist_id, [track_id])


# Friday - tracks from 2022-01-01 onwards are within 6 days
@freeze_time("2022-01-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'

    # Mock the Spotify client - all tracks within the 6-day window
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [{'added_at': '2022-01-07T00:00:00Z', 'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
            'next': 'next_url'
        }
    }
    mock_sp.next.side_effect = [
        {
            'items': [{'added_at': '2022-01-06T00:00:00Z', 'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
            'next': None
        },
        None
    ]

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert len(result) == 2


@freeze_time("2022-01-07")  # Friday
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist_with_mocked_results(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = 'playlist_id'

    # Mock the Spotify client - both tracks within window
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [{'added_at': '2022-01-07T00:00:00Z', 'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
            'next': 'next_url'
        }
    }
    mock_sp.next.side_effect = [
        {
            'items': [{'added_at': '2022-01-06T00:00:00Z', 'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
            'next': None
        },
        None
    ]

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert result == [
        {'name': 'Song 1', 'url': 'url1', 'track_id': 'id1'},
        {'name': 'Song 2', 'url': 'url2', 'track_id': 'id2'}
    ]


@freeze_time("2022-01-07")  # Friday
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist_filters_by_rolling_window(mock_get_spotify_access_token):
    """
    Test that get_playlist only returns tracks within the 6-day rolling window.
    
    This allows songs that were added more than 6 days ago to "come back"
    if someone shares them again in Slack.
    """
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = 'playlist_id'

    # Mock the Spotify client with tracks from different dates
    # Jan 7 = today, Jan 1 = 6 days ago (included), Dec 31 = 7 days ago (excluded)
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [
                {'added_at': '2022-01-07T12:00:00Z', 'track': {'name': 'Today Song',
                                                               'external_urls': {'spotify': 'url1'}, 'id': 'id1'}},
                {'added_at': '2022-01-01T12:00:00Z', 'track': {'name': '6 Days Ago Song',
                                                               'external_urls': {'spotify': 'url2'}, 'id': 'id2'}},
                {'added_at': '2021-12-31T12:00:00Z', 'track': {'name': '7 Days Ago Song',
                                                               'external_urls': {'spotify': 'url3'}, 'id': 'id3'}},
                {'added_at': '2021-11-07T12:00:00Z', 'track': {'name': '2 Months Ago Song',
                                                               'external_urls': {'spotify': 'url4'}, 'id': 'id4'}}
            ],
            'next': None
        }
    }

    # Act
    result = get_playlist(playlist_id)

    # Assert - only first 2 tracks within 6-day window should be returned
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert len(result) == 2
    track_ids = [t['track_id'] for t in result]
    assert 'id1' in track_ids  # Today
    assert 'id2' in track_ids  # 6 days ago
    assert 'id3' not in track_ids  # 7 days ago - excluded
    assert 'id4' not in track_ids  # 2 months ago - excluded (can come back!)
