import pytest
import re
from unittest.mock import MagicMock, patch, ANY
from utils.spotify_util import (
    add_songs_to_spotify_playlist,
    get_playlist,
    is_track_within_window,
    generate_playlist_name,
    generate_playlist_description,
    extract_year_from_playlist_name,
    find_playlist_by_year,
    create_yearly_playlist,
    get_or_create_yearly_playlist,
    get_current_year,
    get_latest_track_year,
)
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
    def test_track_from_6_days_ago_at_midnight_is_included(self):
        """Track added exactly at midnight 6 days ago should be included (exact boundary)."""
        assert is_track_within_window('2022-01-01T00:00:00Z') is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_7_days_ago_is_excluded(self):
        """Track added 7 days ago should be excluded."""
        assert is_track_within_window('2021-12-31T12:00:00Z') is False

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_7_days_ago_at_2359_is_excluded(self):
        """Track added at 23:59 on day 7 (just before midnight) should be excluded."""
        assert is_track_within_window('2021-12-31T23:59:59Z') is False

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


# Tests for yearly playlist management functions
class TestPlaylistNaming:
    """Unit tests for playlist naming functions."""

    @freeze_time("2025-12-07")
    def test_get_current_year(self):
        """Test that get_current_year returns the current year."""
        assert get_current_year() == 2025

    @freeze_time("2025-12-07")
    def test_generate_playlist_name_default_year(self):
        """Test playlist name generation with default (current) year."""
        name = generate_playlist_name()
        # Should extract year correctly and contain 2025
        assert extract_year_from_playlist_name(name) == 2025
        assert '2025' in name
        assert 'Fredagslistan' in name

    def test_generate_playlist_name_specific_year(self):
        """Test playlist name generation with specific year."""
        name_2024 = generate_playlist_name(2024)
        name_2023 = generate_playlist_name(2023)

        # Both should extract correctly and contain their respective years
        assert extract_year_from_playlist_name(name_2024) == 2024
        assert '2024' in name_2024
        assert extract_year_from_playlist_name(name_2023) == 2023
        assert '2023' in name_2023

    @freeze_time("2025-12-07")
    def test_generate_playlist_description_default_year(self):
        """Test playlist description generation with default year."""
        description = generate_playlist_description()
        # Should contain the year
        assert '2025' in description

    def test_generate_playlist_description_specific_year(self):
        """Test playlist description generation with specific year."""
        desc_2024 = generate_playlist_description(2024)
        assert '2024' in desc_2024

    def test_extract_year_from_playlist_name_valid(self):
        """Test extracting year from valid playlist names."""
        # New format with emojis
        assert extract_year_from_playlist_name("Fredagslistan 2025 🎵") == 2025
        assert extract_year_from_playlist_name("Fredagslistan 2024 🔥") == 2024
        assert extract_year_from_playlist_name("Fredagslistan 2023 ✨") == 2023
        # Plain format also works
        assert extract_year_from_playlist_name("Fredagslistan 2025") == 2025
        assert extract_year_from_playlist_name("Fredagslistan 2000") == 2000
        # Old format with exclamation marks (edge case)
        assert extract_year_from_playlist_name("Fredagslistan 2025 !") == 2025

    def test_extract_year_from_playlist_name_invalid(self):
        """Test extracting year from invalid playlist names."""
        # Missing Fredagslistan prefix
        assert extract_year_from_playlist_name("My Playlist 2025") is None
        assert extract_year_from_playlist_name("2025 Fredagslistan") is None
        # No year
        assert extract_year_from_playlist_name("Fredagslistan") is None
        assert extract_year_from_playlist_name("My Playlist") is None
        assert extract_year_from_playlist_name("") is None
        # Note: "Fredagslistan2025" now matches (pattern is more permissive)

    def test_extract_year_from_old_format(self):
        """Test extracting year from old naming convention with exclamation marks.
        
        Multi-year formats like "2024-25" extract the LATEST year (2025).
        """
        # Old format: "Fredagslistan ! 2024-25 !" -> extracts 2025 (the latest year)
        assert extract_year_from_playlist_name(
            "Fredagslistan ! 2024-25 !") == 2025
        assert extract_year_from_playlist_name(
            "Fredagslistan! 2023-24!") == 2024
        # Single year format still works
        assert extract_year_from_playlist_name(
            "Fredagslistan ! 2022 !") == 2022

    def test_extract_year_from_multi_year_format(self):
        """Test extracting year from multi-year formats."""
        # "YYYY-YY" format extracts the latest year
        assert extract_year_from_playlist_name("Fredagslistan 2024-25") == 2025
        assert extract_year_from_playlist_name("Fredagslistan 2019-20") == 2020
        assert extract_year_from_playlist_name(
            "Fredagslistan 1999-00") == 2000  # Century rollover


class TestGetLatestTrackYear:
    """Tests for get_latest_track_year function."""

    @patch('utils.spotify_util.get_spotify_access_token')
    def test_returns_year_from_latest_track(self, mock_get_spotify_access_token):
        """Test extracting year from the most recently added track."""
        mock_sp = MagicMock()
        mock_get_spotify_access_token.return_value = mock_sp

        mock_sp.playlist.return_value = {
            'tracks': {
                'items': [
                    {'added_at': '2024-01-15T10:00:00Z'},
                    {'added_at': '2024-06-20T10:00:00Z'},
                    {'added_at': '2025-01-05T10:00:00Z'},  # Latest
                ]
            }
        }

        result = get_latest_track_year('playlist123')
        assert result == 2025

    @patch('utils.spotify_util.get_spotify_access_token')
    def test_returns_none_for_empty_playlist(self, mock_get_spotify_access_token):
        """Test returns None for playlist with no tracks."""
        mock_sp = MagicMock()
        mock_get_spotify_access_token.return_value = mock_sp

        mock_sp.playlist.return_value = {
            'tracks': {'items': []}
        }

        result = get_latest_track_year('playlist123')
        assert result is None

    @patch('utils.spotify_util.get_spotify_access_token')
    def test_handles_single_track(self, mock_get_spotify_access_token):
        """Test with a single track in the playlist."""
        mock_sp = MagicMock()
        mock_get_spotify_access_token.return_value = mock_sp

        mock_sp.playlist.return_value = {
            'tracks': {
                'items': [{'added_at': '2025-12-01T10:00:00Z'}]
            }
        }

        result = get_latest_track_year('playlist123')
        assert result == 2025

    @patch('utils.spotify_util.get_spotify_access_token')
    def test_finds_latest_across_years(self, mock_get_spotify_access_token):
        """Test finding the latest track when spanning multiple years."""
        mock_sp = MagicMock()
        mock_get_spotify_access_token.return_value = mock_sp

        mock_sp.playlist.return_value = {
            'tracks': {
                'items': [
                    {'added_at': '2023-12-31T23:59:59Z'},
                    {'added_at': '2024-12-15T10:00:00Z'},  # Latest
                    {'added_at': '2024-01-01T00:00:01Z'},
                ]
            }
        }

        result = get_latest_track_year('playlist123')
        assert result == 2024


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_find_playlist_by_year_found(mock_get_spotify_access_token):
    """Test finding an existing playlist by year."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        'items': [
            {
                'id': 'playlist123',
                'name': 'Fredagslistan 2025 🎵',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/playlist123'},
                'description': 'UR pepp 2025 🔥'
            },
            {
                'id': 'other_playlist',
                'name': 'Other Playlist',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/other'},
                'description': 'Some other playlist'
            }
        ],
        'next': None
    }

    # Mock playlist call for track validation
    mock_sp.playlist.return_value = {
        'tracks': {
            'items': [{'added_at': '2025-12-01T10:00:00Z'}]
        }
    }

    result = find_playlist_by_year(2025)

    assert result is not None
    assert result['id'] == 'playlist123'
    assert 'Fredagslistan' in result['name']
    assert '2025' in result['name']
    assert 'playlist123' in result['url']


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_find_playlist_by_year_found_without_validation(mock_get_spotify_access_token):
    """Test finding an existing playlist by year without track validation."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        'items': [
            {
                'id': 'playlist123',
                'name': 'Fredagslistan 2025 🎵',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/playlist123'},
                'description': 'UR pepp 2025 🔥'
            }
        ],
        'next': None
    }

    # Don't need to mock playlist call when validation is disabled
    result = find_playlist_by_year(2025, validate_with_tracks=False)

    assert result is not None
    assert result['id'] == 'playlist123'
    # playlist() should not have been called
    mock_sp.playlist.assert_not_called()


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_find_playlist_by_year_not_found(mock_get_spotify_access_token):
    """Test finding a playlist when it doesn't exist."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        'items': [
            {
                'id': 'old_playlist',
                'name': 'Fredagslistan 2024 🎵',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/old'},
                'description': 'UR pepp 2024 🔥'
            }
        ],
        'next': None
    }

    result = find_playlist_by_year(2025)

    assert result is None


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_find_playlist_by_year_pagination(mock_get_spotify_access_token):
    """Test finding a playlist across multiple pages."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    # First page doesn't have the playlist
    mock_sp.current_user_playlists.side_effect = [
        {
            'items': [{'id': 'p1', 'name': 'Other 1', 'external_urls': {'spotify': 'url1'}, 'description': ''}],
            'next': 'next_url'
        },
        {
            'items': [
                {'id': 'target', 'name': 'Fredagslistan 2025 🔥', 'external_urls': {
                    'spotify': 'url2'}, 'description': 'Fredagsmusik 2025 🎵'}
            ],
            'next': None
        }
    ]

    # Mock playlist call for track validation
    mock_sp.playlist.return_value = {
        'tracks': {'items': [{'added_at': '2025-12-01T10:00:00Z'}]}
    }

    result = find_playlist_by_year(2025)

    assert result is not None
    assert result['id'] == 'target'
    # Should have been called twice for pagination
    assert mock_sp.current_user_playlists.call_count == 2


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_create_yearly_playlist(mock_get_spotify_access_token):
    """Test creating a new yearly playlist."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    mock_sp.current_user.return_value = {'id': 'user123'}
    mock_sp.user_playlist_create.return_value = {
        'id': 'new_playlist_id',
        'name': 'Fredagslistan 2025 🎵',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/new_playlist_id'}
    }

    result = create_yearly_playlist(2025)

    # Verify the call was made with correct structure (name and description are dynamic)
    mock_sp.user_playlist_create.assert_called_once()
    call_kwargs = mock_sp.user_playlist_create.call_args[1]
    assert call_kwargs['user'] == 'user123'
    assert 'Fredagslistan' in call_kwargs['name']
    assert '2025' in call_kwargs['name']
    assert '2025' in call_kwargs['description']
    assert call_kwargs['public'] is True
    assert call_kwargs['collaborative'] is False

    assert result['id'] == 'new_playlist_id'


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_or_create_yearly_playlist_existing(mock_get_spotify_access_token):
    """Test get_or_create when playlist exists."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        'items': [
            {
                'id': 'existing_id',
                'name': 'Fredagslistan 2025 🎧',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/existing_id'},
                'description': 'Fredagsmusik 2025 🔥'
            }
        ],
        'next': None
    }

    result, was_created = get_or_create_yearly_playlist(2025)

    assert was_created is False
    assert result['id'] == 'existing_id'
    # user_playlist_create should NOT have been called
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2025-12-07")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_or_create_yearly_playlist_new(mock_get_spotify_access_token):
    """Test get_or_create when playlist doesn't exist."""
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp

    # No matching playlist found
    mock_sp.current_user_playlists.return_value = {
        'items': [],
        'next': None
    }

    mock_sp.current_user.return_value = {'id': 'user123'}
    mock_sp.user_playlist_create.return_value = {
        'id': 'new_playlist_id',
        'name': 'Fredagslistan 2025 ✨',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/new_playlist_id'}
    }

    result, was_created = get_or_create_yearly_playlist(2025)

    assert was_created is True
    assert result['id'] == 'new_playlist_id'
    mock_sp.user_playlist_create.assert_called_once()
