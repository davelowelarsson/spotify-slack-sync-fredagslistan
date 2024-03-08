import pytest
from unittest.mock import MagicMock, patch
from utils.spotify_util import add_songs_to_spotify_playlist, get_playlist
from datetime import datetime
from freezegun import freeze_time

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


@freeze_time("2022-01-01")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = '1OdSuwMRWtpP0nVhLffEqe'

    # Mock the Spotify client
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [{'added_at': '2022-01-01T00:00:00Z', 'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
            'next': 'next_url'
        }
    }
    mock_sp.next.side_effect = [
        {
            'items': [{'added_at': '2022-01-01T00:00:00Z', 'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
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


@freeze_time("2022-01-01")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist_with_mocked_results(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = 'playlist_id'

    # Mock the Spotify client
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [{'added_at': '2022-01-01T00:00:00Z', 'track': {'name': 'Song 1', 'external_urls': {'spotify': 'url1'}, 'id': 'id1'}}],
            'next': 'next_url'
        }
    }
    mock_sp.next.side_effect = [
        {
            'items': [{'added_at': '2022-01-01T00:00:00Z', 'track': {'name': 'Song 2', 'external_urls': {'spotify': 'url2'}, 'id': 'id2'}}],
            'next': None
        },
        None
    ]

    # Act
    print("Calling get_playlist")
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert result == [
        {'name': 'Song 1', 'url': 'url1', 'track_id': 'id1'},
        {'name': 'Song 2', 'url': 'url2', 'track_id': 'id2'}
    ]


@freeze_time("2022-01-01")
@patch('utils.spotify_util.get_spotify_access_token')
def test_get_playlist_with_one_track_from_today(mock_get_spotify_access_token):
    # Arrange
    mock_sp = MagicMock()
    mock_get_spotify_access_token.return_value = mock_sp
    playlist_id = 'playlist_id'

    # Mock the Spotify client
    mock_sp.playlist.return_value = {
        'name': 'Playlist Name',
        'description': 'Playlist Description',
        'external_urls': {'spotify': 'Playlist URL'},
        'tracks': {
            'items': [
                {'added_at': '2022-01-01T00:00:00Z', 'track': {'name': 'Song 1',
                                                               'external_urls': {'spotify': 'url1'}, 'id': 'id1'}},
                {'added_at': '2021-12-31T00:00:00Z', 'track': {'name': 'Song 2',
                                                               'external_urls': {'spotify': 'url2'}, 'id': 'id2'}},
                {'added_at': '2021-12-31T00:00:00Z', 'track': {'name': 'Song 3',
                                                               'external_urls': {'spotify': 'url3'}, 'id': 'id3'}}
            ],
            'next': None
        }
    }

    # Act
    print("Calling get_playlist")
    result = get_playlist(playlist_id)

    # Assert
    mock_get_spotify_access_token.assert_called_once()
    mock_sp.playlist.assert_called_once_with(playlist_id)
    assert result == [
        {'name': 'Song 1', 'url': 'url1', 'track_id': 'id1'}
    ]
