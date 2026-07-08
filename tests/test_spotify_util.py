from unittest.mock import MagicMock, patch

from freezegun import freeze_time
from spotipy import SpotifyException

from utils.playlist_state import PlaylistAction, PlaylistState
from utils.spotify_util import (
    SearchOutcome,
    add_songs_to_spotify_playlist,
    create_yearly_playlist,
    extract_year_from_playlist_name,
    find_playlist_by_year,
    generate_playlist_description,
    generate_playlist_name,
    get_current_year,
    get_latest_track_year,
    get_playlist,
    is_track_within_window,
    resolve_yearly_playlist,
)


# Unit tests for is_track_within_window
class TestIsTrackWithinWindow:
    """Unit tests for the is_track_within_window function."""

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_today_is_included(self):
        """Track added today should be included."""
        assert is_track_within_window("2022-01-07T12:00:00Z") is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_yesterday_is_included(self):
        """Track added yesterday should be included."""
        assert is_track_within_window("2022-01-06T12:00:00Z") is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_6_days_ago_is_included(self):
        """Track added 6 days ago should be included (boundary)."""
        assert is_track_within_window("2022-01-01T12:00:00Z") is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_6_days_ago_at_midnight_is_included(self):
        """Track added exactly at midnight 6 days ago should be included (exact boundary)."""
        assert is_track_within_window("2022-01-01T00:00:00Z") is True

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_7_days_ago_is_excluded(self):
        """Track added 7 days ago should be excluded."""
        assert is_track_within_window("2021-12-31T12:00:00Z") is False

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_7_days_ago_at_2359_is_excluded(self):
        """Track added at 23:59 on day 7 (just before midnight) should be excluded."""
        assert is_track_within_window("2021-12-31T23:59:59Z") is False

    @freeze_time("2022-01-07")  # Friday
    def test_track_from_2_months_ago_is_excluded(self):
        """Track added 2 months ago should be excluded (can come back!)."""
        assert is_track_within_window("2021-11-07T12:00:00Z") is False


@patch("utils.spotify_util.get_spotify_client")
def test_add_songs_to_spotify_playlist(mock_get_spotify_client):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    playlist_id = "1OdSuwMRWtpP0nVhLffEqe"
    track_ids = ["track1", "track2", "track3"]

    # Act
    add_songs_to_spotify_playlist(playlist_id, track_ids)

    # Assert
    mock_get_spotify_client.assert_called_once()
    mock_sp.playlist_add_items.assert_called_once_with(playlist_id, track_ids)


@patch("utils.spotify_util.get_spotify_client")
def test_add_songs_to_spotify_playlist_single_track(mock_get_spotify_client):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    playlist_id = "1OdSuwMRWtpP0nVhLffEqe"
    track_id = "track1"

    # Act
    add_songs_to_spotify_playlist(playlist_id, track_id)

    # Assert
    mock_get_spotify_client.assert_called_once()
    mock_sp.playlist_add_items.assert_called_once_with(playlist_id, [track_id])


# Friday - tracks from 2022-01-01 onwards are within 6 days
@freeze_time("2022-01-07")
@patch("utils.spotify_util.get_spotify_client")
def test_get_playlist(mock_get_spotify_client):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    playlist_id = "1OdSuwMRWtpP0nVhLffEqe"

    # Mock the Spotify client - all tracks within the 6-day window
    mock_sp.playlist.return_value = {
        "name": "Playlist Name",
        "description": "Playlist Description",
        "external_urls": {"spotify": "Playlist URL"},
        "tracks": {
            "items": [
                {
                    "added_at": "2022-01-07T00:00:00Z",
                    "track": {"name": "Song 1", "external_urls": {"spotify": "url1"}, "id": "id1"},
                }
            ],
            "next": "next_url",
        },
    }
    mock_sp.next.side_effect = [
        {
            "items": [
                {
                    "added_at": "2022-01-06T00:00:00Z",
                    "track": {"name": "Song 2", "external_urls": {"spotify": "url2"}, "id": "id2"},
                }
            ],
            "next": None,
        },
        None,
    ]

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_client.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert len(result) == 2


@freeze_time("2022-01-07")  # Friday
@patch("utils.spotify_util.get_spotify_client")
def test_get_playlist_with_mocked_results(mock_get_spotify_client):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    playlist_id = "playlist_id"

    # Mock the Spotify client - both tracks within window
    mock_sp.playlist.return_value = {
        "name": "Playlist Name",
        "description": "Playlist Description",
        "external_urls": {"spotify": "Playlist URL"},
        "tracks": {
            "items": [
                {
                    "added_at": "2022-01-07T00:00:00Z",
                    "track": {"name": "Song 1", "external_urls": {"spotify": "url1"}, "id": "id1"},
                }
            ],
            "next": "next_url",
        },
    }
    mock_sp.next.side_effect = [
        {
            "items": [
                {
                    "added_at": "2022-01-06T00:00:00Z",
                    "track": {"name": "Song 2", "external_urls": {"spotify": "url2"}, "id": "id2"},
                }
            ],
            "next": None,
        },
        None,
    ]

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_client.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert result == [
        {"name": "Song 1", "url": "url1", "track_id": "id1"},
        {"name": "Song 2", "url": "url2", "track_id": "id2"},
    ]


@freeze_time("2022-01-07")  # Friday
@patch("utils.spotify_util.get_spotify_client")
def test_get_playlist_filters_by_rolling_window(mock_get_spotify_client):
    """
    Test that get_playlist only returns tracks within the 6-day rolling window.

    This allows songs that were added more than 6 days ago to "come back"
    if someone shares them again in Slack.
    """
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    playlist_id = "playlist_id"

    # Mock the Spotify client with tracks from different dates
    # Jan 7 = today, Jan 1 = 6 days ago (included), Dec 31 = 7 days ago (excluded)
    mock_sp.playlist.return_value = {
        "name": "Playlist Name",
        "description": "Playlist Description",
        "external_urls": {"spotify": "Playlist URL"},
        "tracks": {
            "items": [
                {
                    "added_at": "2022-01-07T12:00:00Z",
                    "track": {
                        "name": "Today Song",
                        "external_urls": {"spotify": "url1"},
                        "id": "id1",
                    },
                },
                {
                    "added_at": "2022-01-01T12:00:00Z",
                    "track": {
                        "name": "6 Days Ago Song",
                        "external_urls": {"spotify": "url2"},
                        "id": "id2",
                    },
                },
                {
                    "added_at": "2021-12-31T12:00:00Z",
                    "track": {
                        "name": "7 Days Ago Song",
                        "external_urls": {"spotify": "url3"},
                        "id": "id3",
                    },
                },
                {
                    "added_at": "2021-11-07T12:00:00Z",
                    "track": {
                        "name": "2 Months Ago Song",
                        "external_urls": {"spotify": "url4"},
                        "id": "id4",
                    },
                },
            ],
            "next": None,
        },
    }

    # Act
    result = get_playlist(playlist_id)

    # Assert - only first 2 tracks within 6-day window should be returned
    mock_get_spotify_client.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert len(result) == 2
    track_ids = [t["track_id"] for t in result]
    assert "id1" in track_ids  # Today
    assert "id2" in track_ids  # 6 days ago
    assert "id3" not in track_ids  # 7 days ago - excluded
    assert "id4" not in track_ids  # 2 months ago - excluded (can come back!)


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
        assert "2025" in name
        assert "Fredagslistan" in name

    def test_generate_playlist_name_specific_year(self):
        """Test playlist name generation with specific year."""
        name_2024 = generate_playlist_name(2024)
        name_2023 = generate_playlist_name(2023)

        # Both should extract correctly and contain their respective years
        assert extract_year_from_playlist_name(name_2024) == 2024
        assert "2024" in name_2024
        assert extract_year_from_playlist_name(name_2023) == 2023
        assert "2023" in name_2023

    @freeze_time("2025-12-07")
    def test_generate_playlist_description_default_year(self):
        """Test playlist description generation with default year."""
        description = generate_playlist_description()
        # Should contain the year
        assert "2025" in description

    def test_generate_playlist_description_specific_year(self):
        """Test playlist description generation with specific year."""
        desc_2024 = generate_playlist_description(2024)
        assert "2024" in desc_2024

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
        assert extract_year_from_playlist_name("Fredagslistan ! 2024-25 !") == 2025
        assert extract_year_from_playlist_name("Fredagslistan! 2023-24!") == 2024
        # Single year format still works
        assert extract_year_from_playlist_name("Fredagslistan ! 2022 !") == 2022

    def test_extract_year_from_multi_year_format(self):
        """Test extracting year from multi-year formats."""
        # "YYYY-YY" format extracts the latest year
        assert extract_year_from_playlist_name("Fredagslistan 2024-25") == 2025
        assert extract_year_from_playlist_name("Fredagslistan 2019-20") == 2020
        assert extract_year_from_playlist_name("Fredagslistan 1999-00") == 2000  # Century rollover


class TestGetLatestTrackYear:
    """Tests for get_latest_track_year function."""

    @patch("utils.spotify_util.get_spotify_client")
    def test_returns_year_from_latest_track(self, mock_get_spotify_client):
        """Test extracting year from the most recently added track."""
        mock_sp = MagicMock()
        mock_get_spotify_client.return_value = mock_sp

        # First call: get total count
        mock_sp.playlist.return_value = {"tracks": {"total": 100}}

        # Second call: get last 3 tracks
        mock_sp.playlist_tracks.return_value = {
            "items": [
                {"added_at": "2024-12-20T10:00:00Z"},
                {"added_at": "2024-12-25T10:00:00Z"},
                {"added_at": "2025-01-05T10:00:00Z"},  # Latest
            ]
        }

        result = get_latest_track_year("playlist123")
        assert result == 2025
        mock_sp.playlist_tracks.assert_called_once_with(
            "playlist123",
            fields="items(added_at)",
            limit=3,
            offset=97,  # 100 - 3
        )

    @patch("utils.spotify_util.get_spotify_client")
    def test_returns_none_for_empty_playlist(self, mock_get_spotify_client):
        """Test returns None for playlist with no tracks."""
        mock_sp = MagicMock()
        mock_get_spotify_client.return_value = mock_sp

        mock_sp.playlist.return_value = {"tracks": {"total": 0}}

        result = get_latest_track_year("playlist123")
        assert result is None
        mock_sp.playlist_tracks.assert_not_called()

    @patch("utils.spotify_util.get_spotify_client")
    def test_handles_single_track(self, mock_get_spotify_client):
        """Test with a single track in the playlist."""
        mock_sp = MagicMock()
        mock_get_spotify_client.return_value = mock_sp

        mock_sp.playlist.return_value = {"tracks": {"total": 1}}
        mock_sp.playlist_tracks.return_value = {"items": [{"added_at": "2025-12-01T10:00:00Z"}]}

        result = get_latest_track_year("playlist123")
        assert result == 2025
        mock_sp.playlist_tracks.assert_called_once_with(
            "playlist123",
            fields="items(added_at)",
            limit=3,
            offset=0,  # max(0, 1-3) = 0
        )

    @patch("utils.spotify_util.get_spotify_client")
    def test_handles_large_playlist_efficiently(self, mock_get_spotify_client):
        """Test that a 1200-track playlist only fetches the last 3 tracks."""
        mock_sp = MagicMock()
        mock_get_spotify_client.return_value = mock_sp

        mock_sp.playlist.return_value = {"tracks": {"total": 1200}}
        mock_sp.playlist_tracks.return_value = {
            "items": [
                {"added_at": "2025-12-05T10:00:00Z"},
                {"added_at": "2025-12-06T10:00:00Z"},
                {"added_at": "2025-12-07T10:00:00Z"},  # Latest
            ]
        }

        result = get_latest_track_year("playlist123")
        assert result == 2025
        mock_sp.playlist_tracks.assert_called_once_with(
            "playlist123",
            fields="items(added_at)",
            limit=3,
            offset=1197,  # 1200 - 3
        )


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_found(mock_get_spotify_client):
    """Test finding an existing playlist by year."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "playlist123",
                "name": "Fredagslistan 2025 🎵",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist123"},
                "description": "UR pepp 2025 🔥",
            },
            {
                "id": "other_playlist",
                "name": "Other Playlist",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/other"},
                "description": "Some other playlist",
            },
        ],
        "next": None,
    }

    # Mock playlist calls for track validation (two-step: get total, then get last tracks)
    mock_sp.playlist.return_value = {"tracks": {"total": 50}}
    mock_sp.playlist_tracks.return_value = {"items": [{"added_at": "2025-12-01T10:00:00Z"}]}

    result = find_playlist_by_year(2025)

    assert result.outcome is SearchOutcome.FOUND
    assert result.candidate is not None
    assert result.candidate["id"] == "playlist123"
    assert "Fredagslistan" in result.candidate["name"]
    assert "2025" in result.candidate["name"]
    assert "playlist123" in result.candidate["url"]


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_found_without_validation(mock_get_spotify_client):
    """Test finding an existing playlist by year without track validation."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "playlist123",
                "name": "Fredagslistan 2025 🎵",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist123"},
                "description": "UR pepp 2025 🔥",
            }
        ],
        "next": None,
    }

    # Don't need to mock playlist call when validation is disabled
    result = find_playlist_by_year(2025, validate_with_tracks=False)

    assert result.outcome is SearchOutcome.FOUND
    assert result.candidate is not None
    assert result.candidate["id"] == "playlist123"
    # playlist() should not have been called
    mock_sp.playlist.assert_not_called()


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_not_found(mock_get_spotify_client):
    """Test finding a playlist when it doesn't exist."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp

    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "old_playlist",
                "name": "Fredagslistan 2024 🎵",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/old"},
                "description": "UR pepp 2024 🔥",
            }
        ],
        "next": None,
    }

    result = find_playlist_by_year(2025)

    assert result.outcome is SearchOutcome.CONFIRMED_ABSENT
    assert result.candidate is None


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_pagination(mock_get_spotify_client):
    """Test finding a playlist across multiple pages."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp

    # First page doesn't have the playlist
    mock_sp.current_user_playlists.side_effect = [
        {
            "items": [
                {
                    "id": "p1",
                    "name": "Other 1",
                    "external_urls": {"spotify": "url1"},
                    "description": "",
                }
            ],
            "next": "next_url",
        },
        {
            "items": [
                {
                    "id": "target",
                    "name": "Fredagslistan 2025 🔥",
                    "external_urls": {"spotify": "url2"},
                    "description": "Fredagsmusik 2025 🎵",
                }
            ],
            "next": None,
        },
    ]

    # Mock playlist calls for track validation (two-step: get total, then get last tracks)
    mock_sp.playlist.return_value = {"tracks": {"total": 50}}
    mock_sp.playlist_tracks.return_value = {"items": [{"added_at": "2025-12-01T10:00:00Z"}]}

    result = find_playlist_by_year(2025)

    assert result.outcome is SearchOutcome.FOUND
    assert result.candidate is not None
    assert result.candidate["id"] == "target"
    # Should have been called twice for pagination
    assert mock_sp.current_user_playlists.call_count == 2


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_create_yearly_playlist(mock_get_spotify_client):
    """Test creating a new yearly playlist."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp

    mock_sp.current_user.return_value = {"id": "user123"}
    mock_sp.user_playlist_create.return_value = {
        "id": "new_playlist_id",
        "name": "Fredagslistan 2025 🎵",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/new_playlist_id"},
    }

    result = create_yearly_playlist(2025)

    # Verify the call was made with correct structure (name and description are dynamic)
    mock_sp.user_playlist_create.assert_called_once()
    call_kwargs = mock_sp.user_playlist_create.call_args[1]
    assert call_kwargs["user"] == "user123"
    assert "Fredagslistan" in call_kwargs["name"]
    assert "2025" in call_kwargs["name"]
    assert "2025" in call_kwargs["description"]
    assert call_kwargs["public"] is True
    assert call_kwargs["collaborative"] is False

    assert result["id"] == "new_playlist_id"


@freeze_time("2025-12-07")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_uncertain_on_persistent_error(mock_get_spotify_client):
    """Enumeration that never succeeds must be UNCERTAIN, never CONFIRMED_ABSENT."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.side_effect = SpotifyException(500, -1, "boom")

    with patch("utils.spotify_util.time.sleep"):
        result = find_playlist_by_year(2025)

    assert result.outcome is SearchOutcome.UNCERTAIN
    assert result.candidate is None


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_empty_interior_page_does_not_end_walk(mock_get_spotify_client):
    """An empty INTERIOR page (items=[] with a non-null next) must not stop the
    walk; a match on a later page is still FOUND, never a false CONFIRMED_ABSENT
    that would trigger a duplicate create."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.side_effect = [
        {"items": [], "next": "page2"},  # empty interior page
        {
            "items": [
                {
                    "id": "real2026",
                    "name": "Fredagslistan 2026 🎵",
                    "external_urls": {"spotify": "u"},
                    "description": "",
                    "tracks": {"total": 3},
                }
            ],
            "next": None,
        },
    ]

    result = find_playlist_by_year(2026, validate_with_tracks=False)

    assert result.outcome is SearchOutcome.FOUND
    assert result.candidate is not None
    assert result.candidate["id"] == "real2026"
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_find_playlist_by_year_malformed_page_is_uncertain(mock_get_spotify_client):
    """A page missing the `items` key can't prove completeness -> UNCERTAIN."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.return_value = {"next": None}  # no "items" key

    result = find_playlist_by_year(2026)

    assert result.outcome is SearchOutcome.UNCERTAIN
    mock_sp.user_playlist_create.assert_not_called()


# =============================================================================
# resolve_yearly_playlist — the hardened resolution algorithm
# =============================================================================


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_uses_cached_playlist_without_enumerating(mock_get_spotify_client):
    """state.year == current year and id verifies -> USED_CACHED, no search."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.playlist.return_value = {
        "id": "cached123",
        "name": "Fredagslistan 2026 🎵",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/cached123"},
        "description": "d",
        "tracks": {"total": 12},
    }

    state = PlaylistState(
        playlist_id="cached123", playlist_year=2026, search_failures=2, failure_threshold=5
    )
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.USED_CACHED
    assert result.playlist is not None
    assert result.playlist["id"] == "cached123"
    assert result.was_created is False
    assert result.search_failures == 0  # reset on clean run
    assert result.exit_code == 0
    # No enumeration and no creation on the cached happy path.
    mock_sp.current_user_playlists.assert_not_called()
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_year_rollover_ignores_stale_cache_and_creates(mock_get_spotify_client):
    """Year rollover: a cached id from LAST year is ignored (never verified);
    the hardened search confirms no current-year playlist -> a new one is created.

    This is the core rollover guarantee: last year's cached id must not be
    reused, and the search must still run (not be skipped) before creating.
    """
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    # Only a previous-year playlist exists -> CONFIRMED_ABSENT for 2026.
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "last_year",
                "name": "Fredagslistan 2025 🎵",
                "external_urls": {"spotify": "u"},
                "description": "",
            }
        ],
        "next": None,
    }
    mock_sp.current_user.return_value = {"id": "user1"}
    mock_sp.user_playlist_create.return_value = {
        "id": "new2026",
        "name": "Fredagslistan 2026 ✨",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/new2026"},
    }

    # Cached state is for LAST year -> must be ignored, not verified.
    state = PlaylistState(playlist_id="last_year", playlist_year=2025, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.CREATED
    assert result.was_created is True
    assert result.playlist["id"] == "new2026"
    assert result.playlist_year == 2026
    # The stale cached id was never even verified — we skipped straight to search.
    mock_sp.playlist.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_cache_verify_failure_falls_back_to_search(mock_get_spotify_client):
    """If verifying the cached id raises, fall through to search and FOUND it."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    # Every sp.playlist(...) raises -> verification fails, get_latest_track_year also None.
    mock_sp.playlist.side_effect = SpotifyException(404, -1, "not found")
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "found1",
                "name": "Fredagslistan 2026 🔥",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/found1"},
                "description": "",
                "tracks": {"total": 4},
            }
        ],
        "next": None,
    }

    state = PlaylistState(playlist_id="stale", playlist_year=2026, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.FOUND
    assert result.playlist is not None
    assert result.playlist["id"] == "found1"
    assert result.was_created is False
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_cached_trusts_id_when_name_has_no_year(mock_get_spotify_client):
    """A cached id whose name no longer encodes a year is still trusted (matched
    by id), so a harmless rename that drops the year does not cause a duplicate."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.playlist.return_value = {
        "id": "cached123",
        "name": "Fredagslistan 🎵",  # year dropped by a rename
        "external_urls": {"spotify": "https://open.spotify.com/playlist/cached123"},
        "description": "",
        "tracks": {"total": 20},
    }

    state = PlaylistState(playlist_id="cached123", playlist_year=2026, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.USED_CACHED
    assert result.playlist["id"] == "cached123"
    mock_sp.current_user_playlists.assert_not_called()  # trusted by id, no search
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_cached_rejected_when_name_encodes_different_year(mock_get_spotify_client):
    """A cached id whose name now encodes a DIFFERENT year is rejected -> search."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    # Cached id verification returns a name for the wrong year.
    mock_sp.playlist.return_value = {
        "id": "cached123",
        "name": "Fredagslistan 2024 🎵",
        "external_urls": {"spotify": "u"},
        "description": "",
        "tracks": {"total": 5},
    }
    # Search then confirms no 2026 playlist -> create.
    mock_sp.current_user_playlists.return_value = {"items": [], "next": None}
    mock_sp.current_user.return_value = {"id": "user1"}
    mock_sp.user_playlist_create.return_value = {
        "id": "new2026",
        "name": "Fredagslistan 2026 ✨",
        "external_urls": {"spotify": "u2"},
    }

    state = PlaylistState(playlist_id="cached123", playlist_year=2026, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.CREATED
    mock_sp.current_user_playlists.assert_called()  # cache rejected -> searched


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_found_via_search(mock_get_spotify_client):
    """No cached state but search finds the year -> FOUND, no create."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "search_hit",
                "name": "Fredagslistan 2026 🎶",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/search_hit"},
                "description": "",
                "tracks": {"total": 8},
            }
        ],
        "next": None,
    }
    # Single-candidate validation checks the latest track year (informational).
    mock_sp.playlist.return_value = {"tracks": {"total": 8}}
    mock_sp.playlist_tracks.return_value = {"items": [{"added_at": "2026-05-01T10:00:00Z"}]}

    state = PlaylistState(failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.FOUND
    assert result.playlist["id"] == "search_hit"
    assert result.search_failures == 0
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_confirmed_absent_creates_playlist(mock_get_spotify_client):
    """Enumeration succeeded, no match -> CONFIRMED_ABSENT -> CREATED."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {
                "id": "unrelated",
                "name": "Fredagslistan 2024 🎵",
                "external_urls": {"spotify": "u"},
                "description": "",
            }
        ],
        "next": None,
    }
    mock_sp.current_user.return_value = {"id": "user1"}
    mock_sp.user_playlist_create.return_value = {
        "id": "created1",
        "name": "Fredagslistan 2026 ✨",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/created1"},
    }

    state = PlaylistState(search_failures=1, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.CREATED
    assert result.was_created is True
    assert result.playlist["id"] == "created1"
    assert result.playlist_year == 2026
    assert result.search_failures == 0
    assert result.exit_code == 0
    mock_sp.user_playlist_create.assert_called_once()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_uncertain_never_creates_and_increments(mock_get_spotify_client):
    """THE KEY GUARANTEE: a search that cannot prove absence never creates."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.side_effect = SpotifyException(500, -1, "boom")

    # Stale year forces cache miss -> hardened search -> UNCERTAIN.
    state = PlaylistState(
        playlist_id="prev", playlist_year=2025, search_failures=2, failure_threshold=5
    )
    with patch("utils.spotify_util.time.sleep"):
        result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.ABORTED
    assert result.playlist is None
    assert result.was_created is False
    assert result.playlist_id == "prev"  # prior state preserved
    assert result.playlist_year == 2025
    assert result.search_failures == 3  # incremented
    assert result.exit_code == 0  # below threshold
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_uncertain_at_threshold_sets_exit_code_one(mock_get_spotify_client):
    """When failures reach the threshold, exit_code flips to 1 (red build)."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.side_effect = SpotifyException(500, -1, "boom")

    state = PlaylistState(
        playlist_id="prev", playlist_year=2025, search_failures=4, failure_threshold=5
    )
    with patch("utils.spotify_util.time.sleep"):
        result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.ABORTED
    assert result.search_failures == 5
    assert result.exit_code == 1
    mock_sp.user_playlist_create.assert_not_called()


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_search_retries_then_succeeds(mock_get_spotify_client):
    """A transient error followed by success must NOT be treated as uncertain."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.current_user_playlists.side_effect = [
        SpotifyException(500, -1, "transient"),
        {
            "items": [
                {
                    "id": "retry_hit",
                    "name": "Fredagslistan 2026 🎧",
                    "external_urls": {"spotify": "u"},
                    "description": "",
                    "tracks": {"total": 3},
                }
            ],
            "next": None,
        },
    ]
    # Single-candidate validation checks the latest track year (informational).
    mock_sp.playlist.return_value = {"tracks": {"total": 3}}
    mock_sp.playlist_tracks.return_value = {"items": [{"added_at": "2026-05-01T10:00:00Z"}]}

    state = PlaylistState(failure_threshold=5)
    with patch("utils.spotify_util.time.sleep") as mock_sleep:
        result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.FOUND
    assert result.playlist["id"] == "retry_hit"
    assert mock_sleep.called  # backoff happened between attempts


@freeze_time("2026-07-03")
@patch("utils.spotify_util.get_spotify_client")
def test_resolve_sanity_check_warns_on_zero_tracks(mock_get_spotify_client, capsys):
    """Resolving to an EXISTING but empty playlist warns, does not recreate."""
    mock_sp = MagicMock()
    mock_get_spotify_client.return_value = mock_sp
    mock_sp.playlist.return_value = {
        "id": "cached_empty",
        "name": "Fredagslistan 2026 🎵",
        "external_urls": {"spotify": "u"},
        "description": "",
        "tracks": {"total": 0},
    }

    state = PlaylistState(playlist_id="cached_empty", playlist_year=2026, failure_threshold=5)
    result = resolve_yearly_playlist(state)

    assert result.action is PlaylistAction.USED_CACHED
    out = capsys.readouterr().out
    assert "0 tracks" in out
    # A zero-track anomaly must never trigger a duplicate create.
    mock_sp.user_playlist_create.assert_not_called()


# =============================================================================
# PLAYLIST_NAME_PREFIX_PATTERN regex fix (leading emoji / whitespace tolerance)
# =============================================================================


class TestPlaylistNamePrefixRegex:
    """The prefix pattern must tolerate leading emoji/space without over-matching."""

    def test_leading_emoji_matches(self):
        assert extract_year_from_playlist_name("🎵 Fredagslistan 2026") == 2026

    def test_leading_and_trailing_whitespace_matches(self):
        assert extract_year_from_playlist_name(" Fredagslistan 2025 ") == 2025

    def test_multi_year_format_matches(self):
        assert extract_year_from_playlist_name("Fredagslistan 2024-25") == 2025

    def test_embedded_fredagslistan_does_not_match(self):
        # "My Fredagslistan clone" is a different playlist, not ours.
        assert extract_year_from_playlist_name("My Fredagslistan clone") is None

    def test_unrelated_name_with_year_does_not_match(self):
        assert extract_year_from_playlist_name("Random 2026") is None

    def test_leading_digit_does_not_match(self):
        # A year before the word must not be accepted as our prefix.
        assert extract_year_from_playlist_name("2026 Fredagslistan") is None

    def test_longer_word_with_prefix_does_not_match(self):
        # "Fredagslistanish" merely starts with the prefix; the trailing \b
        # boundary must reject it so we don't adopt an unrelated playlist.
        assert extract_year_from_playlist_name("Fredagslistanish 2026") is None
