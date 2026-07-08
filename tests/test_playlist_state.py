"""Tests for the pure playlist_state module (no spotipy / no network)."""

from utils.playlist_state import (
    DEFAULT_FAILURE_THRESHOLD,
    PlaylistAction,
    PlaylistState,
    ResolutionResult,
    abort_result,
    read_state_from_env,
    success_result,
    write_github_output,
)


class TestReadStateFromEnv:
    """read_state_from_env should tolerate absent / blank / invalid values."""

    def test_empty_env_returns_defaults(self):
        state = read_state_from_env({})
        assert state.playlist_id is None
        assert state.playlist_year is None
        assert state.search_failures == 0
        assert state.failure_threshold == DEFAULT_FAILURE_THRESHOLD

    def test_reads_all_values(self):
        state = read_state_from_env(
            {
                "FREDAGSLISTAN_PLAYLIST_ID": "abc123",
                "FREDAGSLISTAN_PLAYLIST_YEAR": "2026",
                "FREDAGSLISTAN_SEARCH_FAILURES": "3",
                "FREDAGSLISTAN_FAILURE_THRESHOLD": "7",
            }
        )
        assert state.playlist_id == "abc123"
        assert state.playlist_year == 2026
        assert state.search_failures == 3
        assert state.failure_threshold == 7

    def test_blank_strings_treated_as_absent(self):
        state = read_state_from_env(
            {"FREDAGSLISTAN_PLAYLIST_ID": "", "FREDAGSLISTAN_PLAYLIST_YEAR": "   "}
        )
        assert state.playlist_id is None
        assert state.playlist_year is None

    def test_invalid_ints_fall_back_to_defaults(self):
        state = read_state_from_env(
            {
                "FREDAGSLISTAN_SEARCH_FAILURES": "not-a-number",
                "FREDAGSLISTAN_FAILURE_THRESHOLD": "",
            }
        )
        assert state.search_failures == 0
        assert state.failure_threshold == DEFAULT_FAILURE_THRESHOLD

    def test_whitespace_is_stripped(self):
        state = read_state_from_env(
            {"FREDAGSLISTAN_PLAYLIST_ID": "  pid  ", "FREDAGSLISTAN_PLAYLIST_YEAR": " 2025 "}
        )
        assert state.playlist_id == "pid"
        assert state.playlist_year == 2025


class TestAbortResult:
    """abort_result implements the UNCERTAIN counter/threshold logic."""

    def test_increments_failures_exit_zero_below_threshold(self):
        state = PlaylistState(
            playlist_id="prev", playlist_year=2026, search_failures=0, failure_threshold=5
        )
        result = abort_result(state)
        assert result.action is PlaylistAction.ABORTED
        assert result.playlist is None
        assert result.was_created is False
        assert result.playlist_id == "prev"  # prior state kept
        assert result.playlist_year == 2026
        assert result.search_failures == 1
        assert result.exit_code == 0

    def test_exit_one_when_reaching_threshold(self):
        state = PlaylistState(
            playlist_id="prev", playlist_year=2026, search_failures=4, failure_threshold=5
        )
        result = abort_result(state)
        assert result.search_failures == 5
        assert result.exit_code == 1

    def test_exit_one_when_above_threshold(self):
        state = PlaylistState(search_failures=9, failure_threshold=5)
        result = abort_result(state)
        assert result.search_failures == 10
        assert result.exit_code == 1


class TestSuccessResult:
    """success_result resets the counter and always exits 0."""

    def test_resets_failures_and_exit_zero(self):
        state = PlaylistState(search_failures=4, failure_threshold=5)
        playlist = {"id": "new", "name": "Fredagslistan 2026 🎵"}
        result = success_result(state, PlaylistAction.FOUND, playlist, 2026)
        assert result.action is PlaylistAction.FOUND
        assert result.playlist_id == "new"
        assert result.playlist_year == 2026
        assert result.search_failures == 0
        assert result.exit_code == 0
        assert result.was_created is False

    def test_created_sets_was_created(self):
        state = PlaylistState(failure_threshold=5)
        playlist = {"id": "created", "name": "Fredagslistan 2026 ✨"}
        result = success_result(state, PlaylistAction.CREATED, playlist, 2026, was_created=True)
        assert result.action is PlaylistAction.CREATED
        assert result.was_created is True
        assert result.exit_code == 0


class TestWriteGithubOutput:
    """write_github_output is a no-op locally and KEY=value lines in CI."""

    def _result(self):
        return ResolutionResult(
            action=PlaylistAction.CREATED,
            playlist={"id": "x", "name": "n"},
            playlist_id="x",
            playlist_year=2026,
            search_failures=0,
            failure_threshold=5,
            was_created=True,
            exit_code=0,
        )

    def test_no_op_when_github_output_unset(self):
        assert write_github_output(self._result(), env={}) is False

    def test_writes_expected_key_value_lines(self, tmp_path):
        out = tmp_path / "out.txt"
        assert write_github_output(self._result(), env={"GITHUB_OUTPUT": str(out)}) is True
        content = out.read_text(encoding="utf-8")
        assert "action=CREATED" in content
        assert "exit_code=0" in content
        assert "playlist_id=x" in content
        assert "playlist_year=2026" in content
        assert "search_failures=0" in content
        assert "was_created=true" in content

    def test_aborted_writes_empty_playlist_id_and_incremented_counter(self, tmp_path):
        out = tmp_path / "out.txt"
        state = PlaylistState(playlist_id=None, playlist_year=None, search_failures=4)
        result = abort_result(state)
        write_github_output(result, env={"GITHUB_OUTPUT": str(out)})
        content = out.read_text(encoding="utf-8")
        assert "action=ABORTED" in content
        assert "playlist_id=\n" in content or "playlist_id=" in content
        assert "search_failures=5" in content

    def test_appends_rather_than_truncates(self, tmp_path):
        out = tmp_path / "out.txt"
        out.write_text("preexisting=1\n", encoding="utf-8")
        write_github_output(self._result(), env={"GITHUB_OUTPUT": str(out)})
        content = out.read_text(encoding="utf-8")
        assert "preexisting=1" in content
        assert "action=CREATED" in content
