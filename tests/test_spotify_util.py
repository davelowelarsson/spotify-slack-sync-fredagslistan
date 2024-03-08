import pytest
from unittest.mock import MagicMock, patch, Mock
from utils.spotify_util import add_songs_to_spotify_playlist, get_playlist
from datetime import datetime

# @patch('utils.spotify_util.get_spotify_access_token')
# def test_add_songs_to_spotify_playlist(mock_get_spotify_access_token):
#     # Arrange
#     mock_sp = MagicMock()
#     mock_get_spotify_access_token.return_value = mock_sp
#     playlist_id = '1OdSuwMRWtpP0nVhLffEqe'
#     track_ids = ['track1', 'track2', 'track3']

#     # Act
#     add_songs_to_spotify_playlist(playlist_id, track_ids)

#     # Assert
#     mock_get_spotify_access_token.assert_called_once()
#     mock_sp.playlist_add_items.assert_called_once_with(playlist_id, track_ids)


# @patch('utils.spotify_util.get_spotify_access_token')
# def test_add_songs_to_spotify_playlist_single_track(mock_get_spotify_access_token):
#     # Arrange
#     mock_sp = MagicMock()
#     mock_get_spotify_access_token.return_value = mock_sp
#     playlist_id = '1OdSuwMRWtpP0nVhLffEqe'
#     track_id = 'track1'

#     # Act
#     add_songs_to_spotify_playlist(playlist_id, track_id)

#     # Assert
#     mock_get_spotify_access_token.assert_called_once()
#     mock_sp.playlist_add_items.assert_called_once_with(playlist_id, [track_id])


# @patch('utils.spotify_util.get_spotify_access_token')
# def test_get_playlist(mock_get_spotify_access_token):
#     # Arrange
#     mock_sp = MagicMock()
#     mock_get_spotify_access_token.return_value = mock_sp
#     playlist_id = '1OdSuwMRWtpP0nVhLffEqe'

#     # Act
#     result = get_playlist(playlist_id)

#     # Assert
#     mock_get_spotify_access_token.assert_called_once()
#     mock_sp.playlist.assert_called_once_with(playlist_id)
#     # Update the expected length based on the number of songs added today
#     assert len(result) == 2
#     # Add more assertions based on the expected behavior of your get_playlist function


# patch('spotify_util.get_spotify_access_token')
# def test_get_playlist(mock_get_spotify_access_token):
#     # Mock the Spotify client
#     mock_spotify = Mock()
#     mock_get_spotify_access_token.return_value = mock_spotify

#     # Mock the first page of results
#     mock_spotify.playlist.return_value = {
#         'tracks': {
#             'items': [{'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
#             'next': 'next_url'
#         }
#     }

#     # Mock the second page of results
#     mock_spotify.next.return_value = {
#         'items': [{'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
#         'next': None
#     }

#     # Call the function
#     songs = get_playlist('playlist_id')

#     # Check the results
#     assert songs == [
#         {'name': 'Song 1', 'url': 'url1', 'track_id': 'id1'},
#         {'name': 'Song 2', 'url': 'url2', 'track_id': 'id2'}
#     ]

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


# @patch('utils.spotify_util.get_spotify_access_token')
# def test_get_playlist(mock_get_spotify_access_token):
#     # Arrange
#     mock_sp = MagicMock()
#     mock_get_spotify_access_token.return_value = mock_sp
#     playlist_id = '1OdSuwMRWtpP0nVhLffEqe'

#     # Act
#     result = get_playlist(playlist_id)

#     # Assert
#     mock_get_spotify_access_token.assert_called_once()
#     mock_sp.playlist.assert_called_once_with(playlist_id)
#     # Update the expected length based on the number of songs added today
#     assert len(result) == 2
#     # Add more assertions based on the expected behavior of your get_playlist function


# @patch('utils.spotify_util.get_spotify_access_token')
# def test_get_playlist_with_mocked_results(mock_get_spotify_access_token):
#     # Arrange
#     mock_sp = MagicMock()
#     mock_get_spotify_access_token.return_value = mock_sp
#     playlist_id = 'playlist_id'

#     # Mock the Spotify client
#     mock_sp.playlist.return_value = {
#         'name': 'Playlist Name',
#         'description': 'Playlist Description',
#         'external_urls': {'spotify': 'Playlist URL'},
#         'tracks': {
#             'items': [{'added_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), 'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
#             'next': 'next_url'
#         }
#     }
#     mock_sp.next.return_value = {
#         'items': [{'added_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), 'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
#         'next': None
#     }

#     # Act
#     result = get_playlist(playlist_id)

#     # Assert
#     mock_get_spotify_access_token.assert_called_once()
#     mock_sp.playlist.assert_called_once_with(playlist_id)
#     assert result == [
#         {'name': 'Song 1', 'url': 'url1', 'track_id': 'id1'},
#         {'name': 'Song 2', 'url': 'url2', 'track_id': 'id2'}
#     ]
