import pytest
from unittest.mock import MagicMock, patch
from utils.spotify_util import add_songs_to_spotify_playlist


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
