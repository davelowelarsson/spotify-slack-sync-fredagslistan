"""Tests for main() orchestration.

The key guarantee: create + announce is only reachable when a playlist was
actually created (action=CREATED / was_created=True). An ABORTED (UNCERTAIN /
cache-miss) resolution must never announce or add tracks.
"""

from unittest.mock import patch

import main as main_module
from utils.playlist_state import PlaylistAction, ResolutionResult


def _aborted_result():
    return ResolutionResult(
        action=PlaylistAction.ABORTED,
        playlist=None,
        playlist_id="prev",
        playlist_year=2025,
        search_failures=3,
        failure_threshold=5,
        was_created=False,
        exit_code=0,
    )


def _created_result():
    return ResolutionResult(
        action=PlaylistAction.CREATED,
        playlist={
            "id": "new123",
            "name": "Fredagslistan 2026 ✨",
            "url": "https://open.spotify.com/playlist/new123",
        },
        playlist_id="new123",
        playlist_year=2026,
        search_failures=0,
        failure_threshold=5,
        was_created=True,
        exit_code=0,
    )


@patch("main.write_github_output")
@patch("main.add_songs_to_spotify_playlist")
@patch("main.compare_lists_and_remove_duplicates")
@patch("main.announce_new_playlist")
@patch("main.resolve_yearly_playlist")
def test_aborted_never_announces_or_adds(
    mock_resolve, mock_announce, mock_compare, mock_add, mock_write
):
    mock_resolve.return_value = _aborted_result()

    main_module.main()

    # THE KEY GUARANTEE: no create/announce/add on an aborted resolution.
    mock_announce.assert_not_called()
    mock_compare.assert_not_called()
    mock_add.assert_not_called()
    # Output is still emitted so the workflow can persist the incremented counter.
    mock_write.assert_called_once()


@patch("main.write_github_output")
@patch("main.add_songs_to_spotify_playlist")
@patch("main.compare_lists_and_remove_duplicates")
@patch("main.get_previous_year_stats")
@patch("main.announce_new_playlist")
@patch("main.resolve_yearly_playlist")
def test_created_announces_and_syncs(
    mock_resolve, mock_announce, mock_stats, mock_compare, mock_add, mock_write
):
    mock_resolve.return_value = _created_result()
    mock_stats.return_value = None  # skip contributor lookup branch
    mock_compare.return_value = ([], [])
    mock_announce.return_value = (True, True)

    main_module.main()

    mock_announce.assert_called_once()
    mock_compare.assert_called_once()
    mock_add.assert_called_once()
    mock_write.assert_called_once()


@patch("main.write_github_output")
@patch("main.add_songs_to_spotify_playlist")
@patch("main.compare_lists_and_remove_duplicates")
@patch("main.announce_new_playlist")
@patch("main.resolve_yearly_playlist")
def test_found_syncs_but_does_not_announce(
    mock_resolve, mock_announce, mock_compare, mock_add, mock_write
):
    found = ResolutionResult(
        action=PlaylistAction.FOUND,
        playlist={"id": "f1", "name": "Fredagslistan 2026 🎵", "url": "u"},
        playlist_id="f1",
        playlist_year=2026,
        search_failures=0,
        failure_threshold=5,
        was_created=False,
        exit_code=0,
    )
    mock_resolve.return_value = found
    mock_compare.return_value = ([], [])

    main_module.main()

    mock_announce.assert_not_called()
    mock_compare.assert_called_once()
    mock_add.assert_called_once()


def _would_create_result():
    return ResolutionResult(
        action=PlaylistAction.WOULD_CREATE,
        playlist=None,
        playlist_id=None,
        playlist_year=None,
        search_failures=0,
        failure_threshold=5,
        was_created=False,
        exit_code=0,
    )


@patch.dict("os.environ", {"DRY_RUN": "1"})
@patch("main.write_github_output")
@patch("main.add_songs_to_spotify_playlist")
@patch("main.compare_lists_and_remove_duplicates")
@patch("main.announce_new_playlist")
@patch("main.resolve_yearly_playlist")
def test_dry_run_would_create_skips_sync_and_announce_but_writes_output(
    mock_resolve, mock_announce, mock_compare, mock_add, mock_write
):
    """DRY_RUN + WOULD_CREATE (playlist=None): no announce/compare/add, output still written."""
    mock_resolve.return_value = _would_create_result()

    main_module.main()

    mock_resolve.assert_called_once()
    assert mock_resolve.call_args.kwargs["dry_run"] is True
    mock_announce.assert_not_called()
    mock_compare.assert_not_called()
    mock_add.assert_not_called()
    mock_write.assert_called_once()


@patch.dict("os.environ", {"DRY_RUN": "true"})
@patch("main.write_github_output")
@patch("main.add_songs_to_spotify_playlist")
@patch("main.compare_lists_and_remove_duplicates")
@patch("main.announce_new_playlist")
@patch("main.resolve_yearly_playlist")
def test_dry_run_found_reads_but_does_not_write(
    mock_resolve, mock_announce, mock_compare, mock_add, mock_write
):
    """DRY_RUN with an existing (FOUND) playlist: compare runs (read-only), but
    add_songs_to_spotify_playlist / announce (the write calls) are never invoked."""
    found = ResolutionResult(
        action=PlaylistAction.FOUND,
        playlist={"id": "f1", "name": "Fredagslistan 2026 🎵", "url": "u"},
        playlist_id="f1",
        playlist_year=2026,
        search_failures=0,
        failure_threshold=5,
        was_created=False,
        exit_code=0,
    )
    mock_resolve.return_value = found
    mock_compare.return_value = (["track1", "track2"], [])

    main_module.main()

    assert mock_resolve.call_args.kwargs["dry_run"] is True
    mock_announce.assert_not_called()
    mock_compare.assert_called_once()
    mock_add.assert_not_called()
    mock_write.assert_called_once()
