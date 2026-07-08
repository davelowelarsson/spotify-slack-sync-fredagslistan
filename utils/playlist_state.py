"""Pure, network-free durable-state helpers for the Fredagslistan sync.

The Python app never touches the GitHub API. Durable state (the resolved
playlist id/year and a search-failure counter) arrives as environment
variables and is emitted back as GitHub Actions step outputs; the workflow
persists it via ``gh variable set``. This module contains only the state
dataclasses, env parsing, the failure-counter / exit-code logic, and the
output writer -- no spotipy, no network -- so it is trivially unit-testable.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

DEFAULT_FAILURE_THRESHOLD = 5

_DRY_RUN_TRUTHY = {"1", "true", "yes", "on"}


class PlaylistAction(StrEnum):
    """What the resolver decided to do this run."""

    USED_CACHED = "USED_CACHED"
    FOUND = "FOUND"
    CREATED = "CREATED"
    WOULD_CREATE = "WOULD_CREATE"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class PlaylistState:
    """Durable state coming IN from the environment (may be empty locally)."""

    playlist_id: str | None = None
    playlist_year: int | None = None
    search_failures: int = 0
    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD


@dataclass(frozen=True)
class ResolutionResult:
    """The computed new state + action + exit code, ready to emit."""

    action: PlaylistAction
    playlist: dict | None
    playlist_id: str | None
    playlist_year: int | None
    search_failures: int
    failure_threshold: int
    was_created: bool
    exit_code: int


def _parse_int(raw: str | None, default: int) -> int:
    """Parse an int, falling back to ``default`` for blank/invalid input."""
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _parse_optional_int(raw: str | None) -> int | None:
    """Parse an int, returning None for blank/invalid input."""
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def is_dry_run(env: Mapping[str, str] | None = None) -> bool:
    """True when the ``DRY_RUN`` env var is set to a recognised truthy value.

    Case-insensitive, whitespace-tolerant. Absent, blank, or anything else
    (including "0"/"false"/"no"/"off") is False.
    """
    if env is None:
        env = os.environ
    return (env.get("DRY_RUN") or "").strip().lower() in _DRY_RUN_TRUTHY


def read_state_from_env(env: Mapping[str, str] | None = None) -> PlaylistState:
    """Read durable state from environment variables (defaults when absent)."""
    if env is None:
        env = os.environ

    raw_id = (env.get("FREDAGSLISTAN_PLAYLIST_ID") or "").strip()

    return PlaylistState(
        playlist_id=raw_id or None,
        playlist_year=_parse_optional_int(env.get("FREDAGSLISTAN_PLAYLIST_YEAR")),
        search_failures=_parse_int(env.get("FREDAGSLISTAN_SEARCH_FAILURES"), 0),
        failure_threshold=_parse_int(
            env.get("FREDAGSLISTAN_FAILURE_THRESHOLD"), DEFAULT_FAILURE_THRESHOLD
        ),
    )


def success_result(
    state: PlaylistState,
    action: PlaylistAction,
    playlist: dict,
    year: int,
    *,
    was_created: bool = False,
) -> ResolutionResult:
    """Build a clean-run result: adopt the resolved playlist, reset failures."""
    return ResolutionResult(
        action=action,
        playlist=playlist,
        playlist_id=playlist["id"],
        playlist_year=year,
        search_failures=0,
        failure_threshold=state.failure_threshold,
        was_created=was_created,
        exit_code=0,
    )


def abort_result(state: PlaylistState) -> ResolutionResult:
    """Build a safe-abort result on UNCERTAIN: keep prior state, bump counter.

    Never destructive. exit_code becomes 1 once the incremented failure count
    reaches the threshold, so the workflow can turn the build red (email alert)
    -- but only AFTER the counter has been persisted.
    """
    failures = state.search_failures + 1
    return ResolutionResult(
        action=PlaylistAction.ABORTED,
        playlist=None,
        playlist_id=state.playlist_id,
        playlist_year=state.playlist_year,
        search_failures=failures,
        failure_threshold=state.failure_threshold,
        was_created=False,
        exit_code=1 if failures >= state.failure_threshold else 0,
    )


def write_github_output(result: ResolutionResult, env: Mapping[str, str] | None = None) -> bool:
    """Append the result as KEY=value step outputs to ``$GITHUB_OUTPUT``.

    Returns True if written, False when GITHUB_OUTPUT is unset (local run).
    """
    if env is None:
        env = os.environ

    path = env.get("GITHUB_OUTPUT")
    if not path:
        return False

    lines = [
        f"action={result.action.value}",
        f"exit_code={result.exit_code}",
        f"playlist_id={result.playlist_id or ''}",
        f"playlist_year={result.playlist_year if result.playlist_year is not None else ''}",
        f"search_failures={result.search_failures}",
        f"failure_threshold={result.failure_threshold}",
        f"was_created={'true' if result.was_created else 'false'}",
    ]
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return True
