import pytest
from unittest.mock import MagicMock, patch
from utils.spotify_util import add_songs_to_spotify_playlist, get_playlist
from datetime import datetime

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


@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    # Update the expected length based on the number of songs added today
    assert len(result) == 2
    # Add more assertions based on the expected behavior of your get_playlist function


@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'
    mock_sp.playlist.return_value = {
        'name': 'Test Playlist',
        'description': 'This is a test playlist',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/45o1nZW7H9uruWYiR6pz9S?si=c734ae1351a84a9b'},
        'tracks': {
            'items': [
                {
                    'added_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'track': {
                        'name': 'Song 1',
                        'external_urls': {'spotify': 'https://open.spotify.com/track/track1'},
                        'id': 'track1'
                    }
                },
                {
                    'added_at': '2024-02-01T08:18:14Z',
                    'track': {
                        'name': 'Song 2',
                        'external_urls': {'spotify': 'https://open.spotify.com/track/track2'},
                        'id': 'track2'
                    }
                }
            ],
            'total': 2
        }
    }

    # Act
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert len(result) == 1
    assert result[0]['name'] == 'Song 1'
    assert result[0]['url'] == 'https://open.spotify.com/track/track1'
    assert result[0]['track_id'] == 'track1'
