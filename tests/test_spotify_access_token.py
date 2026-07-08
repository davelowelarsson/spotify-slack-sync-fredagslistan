import os
from unittest.mock import patch

from utils.spotify_access_token import _build_auth_manager


@patch("utils.spotify_access_token.SpotifyOAuth")
@patch("utils.spotify_access_token.MemoryCacheHandler")
def test_build_auth_manager_uses_refresh_token_in_memory(mock_cache, mock_oauth):
    """With SPOTIPY_REFRESH_TOKEN set, authenticate from an in-memory cache
    seeded with that token — no file, no browser."""
    with patch.dict(os.environ, {"SPOTIPY_REFRESH_TOKEN": "rt_abc"}, clear=True):
        _build_auth_manager("scope-x")

    mock_cache.assert_called_once()
    token_info = mock_cache.call_args.kwargs["token_info"]
    assert token_info["refresh_token"] == "rt_abc"
    assert token_info["expires_at"] == 0  # already expired -> forces refresh
    assert token_info["scope"] == "scope-x"

    _, kwargs = mock_oauth.call_args
    assert kwargs["cache_handler"] is mock_cache.return_value
    assert kwargs["open_browser"] is False
    assert kwargs["scope"] == "scope-x"


@patch("utils.spotify_access_token.SpotifyOAuth")
@patch("utils.spotify_access_token.MemoryCacheHandler")
def test_build_auth_manager_falls_back_to_default_without_token(mock_cache, mock_oauth):
    """Without a refresh token in the env, use spotipy's default file/interactive
    flow (local development) and never touch the in-memory cache handler."""
    with patch.dict(os.environ, {}, clear=True):
        _build_auth_manager("scope-y")

    mock_cache.assert_not_called()
    mock_oauth.assert_called_once_with(scope="scope-y")
