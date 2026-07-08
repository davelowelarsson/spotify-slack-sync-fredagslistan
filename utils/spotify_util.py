import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from spotipy import SpotifyException

from utils.playlist_state import (
    PlaylistAction,
    PlaylistState,
    ResolutionResult,
    abort_result,
    success_result,
)
from utils.spotify_access_token import get_spotify_client
from utils.texts import (
    PLAYLIST_NAME_PREFIX_PATTERN,
    PLAYLIST_YEAR_PATTERN,
    get_random_playlist_description,
    get_random_playlist_name,
)

# Retry configuration for the hardened playlist enumeration.
_SEARCH_MAX_ATTEMPTS = 3
_SEARCH_BACKOFF_SECONDS = 0.5


class SearchOutcome(Enum):
    """Tri-state result of enumerating the user's playlists for a given year.

    Only CONFIRMED_ABSENT (a fully successful enumeration with no name match)
    ever authorises creating a new playlist. Any API error / incomplete
    enumeration yields UNCERTAIN, which must never lead to a create.
    """

    FOUND = "FOUND"
    CONFIRMED_ABSENT = "CONFIRMED_ABSENT"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class SearchResult:
    """Outcome of :func:`find_playlist_by_year` plus the matched candidate."""

    outcome: SearchOutcome
    candidate: dict | None = None


def _require[T](value: T | None, what: str = "Spotify API response") -> T:
    """Return ``value`` if present, else raise.

    spotipy types its responses as Optional; callers here rely on a real
    response, so surface a clear error instead of an opaque ``NoneType`` crash.
    """
    if value is None:
        raise RuntimeError(f"{what} was unexpectedly empty")
    return value


def get_current_year() -> int:
    """Get the current year."""
    return datetime.now(tz=UTC).year


def get_latest_track_year(playlist_id: str) -> int | None:
    """
    Get the year of the most recently added track in a playlist.

    This is used to validate that a playlist is still active for the
    expected year. For example, if the name suggests 2025 but the last
    track was added in 2024, the playlist is probably for 2024.

    Uses an efficient approach: gets total track count first, then fetches
    only the last few tracks using offset pagination.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        The year of the most recently added track, or None if playlist is empty
    """
    sp = get_spotify_client()

    try:
        # First, get the total track count
        playlist_info = _require(sp.playlist(playlist_id, fields="tracks.total"))
        total_tracks = playlist_info.get("tracks", {}).get("total", 0)

        if total_tracks == 0:
            return None

        # Fetch the last 3 tracks (in case some have missing added_at)
        # Spotify orders tracks by addition order, so last = most recent
        offset = max(0, total_tracks - 3)
        tracks_response = _require(
            sp.playlist_tracks(playlist_id, fields="items(added_at)", limit=3, offset=offset)
        )
        items = tracks_response.get("items", [])

        if not items:
            return None

        # Find the most recent added_at date among the last few tracks
        latest_date = None
        for item in items:
            added_at = item.get("added_at")
            if added_at:
                # Parse ISO 8601 format: "2024-12-06T15:30:00Z"
                track_date = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                if latest_date is None or track_date > latest_date:
                    latest_date = track_date

        if latest_date:
            return latest_date.year

        return None
    except SpotifyException as e:
        print(f"Error fetching playlist tracks: {e}")
        return None


def generate_playlist_name(year: int | None = None) -> str:
    """
    Generate a random playlist name for a given year.

    Args:
        year: The year for the playlist. Defaults to current year.

    Returns:
        Random playlist name containing 'Fredagslistan' and the year
    """
    if year is None:
        year = get_current_year()
    return get_random_playlist_name(year)


def generate_playlist_description(year: int | None = None) -> str:
    """
    Generate a random playlist description for a given year.

    Args:
        year: The year for the playlist. Defaults to current year.

    Returns:
        Random playlist description with the year
    """
    if year is None:
        year = get_current_year()
    return get_random_playlist_description(year)


def extract_year_from_playlist_name(name: str) -> int | None:
    """
    Extract the year from a playlist name.

    Matches any playlist starting with 'Fredagslistan' followed by a year.
    Handles multi-year formats like "2024-25" by extracting the latest year.

    Examples:
        - "Fredagslistan 2025 🎵" -> 2025
        - "Fredagslistan ! 2024-25 !" -> 2025 (extracts 2024, adds suffix 25 -> 2025)
        - "Fredagslistan 2024" -> 2024

    Args:
        name: Playlist name to parse

    Returns:
        The year as an integer, or None if the name doesn't match the pattern
    """
    # First, verify it starts with Fredagslistan
    if not re.match(PLAYLIST_NAME_PREFIX_PATTERN, name):
        return None

    # Find years in the name (handles "2024-25" format)
    match = re.search(PLAYLIST_YEAR_PATTERN, name)
    if match:
        base_year = int(match.group(1))
        suffix = match.group(2)  # e.g., "25" from "2024-25"

        if suffix:
            # Convert 2-digit suffix to full year (e.g., 25 -> 2025)
            # Take century from base_year
            century = (base_year // 100) * 100
            suffix_year = century + int(suffix)

            # Handle century rollover (e.g., 1999-00 -> 2000)
            if suffix_year < base_year:
                suffix_year += 100

            return suffix_year

        return base_year

    return None


def _fetch_playlists_page(sp, limit: int, offset: int) -> dict | None:
    """Fetch one page of the current user's playlists, with retry.

    Returns the page dict on success, or None if every attempt failed. A None
    here means the enumeration is incomplete and its result cannot be trusted.
    """
    last_exc: SpotifyException | None = None
    for attempt in range(1, _SEARCH_MAX_ATTEMPTS + 1):
        try:
            return _require(sp.current_user_playlists(limit=limit, offset=offset))
        except SpotifyException as exc:
            last_exc = exc
            print(
                f"⚠️ Error fetching playlists (offset={offset}, "
                f"attempt {attempt}/{_SEARCH_MAX_ATTEMPTS}): {exc}"
            )
            if attempt < _SEARCH_MAX_ATTEMPTS:
                time.sleep(_SEARCH_BACKOFF_SECONDS)
    print(f"❌ Giving up on playlists page at offset={offset}: {last_exc}")
    return None


def _select_candidate(candidates: list[dict], year: int, validate_with_tracks: bool) -> dict:
    """Choose the best matching candidate among name matches.

    This only runs once enumeration has fully succeeded and at least one name
    matched, so it never affects the FOUND/ABSENT/UNCERTAIN decision.
    """
    if len(candidates) == 1:
        candidate = candidates[0]
        if validate_with_tracks:
            latest_track_year = get_latest_track_year(candidate["id"])
            if latest_track_year is not None and latest_track_year not in (year, year - 1):
                print(
                    f"⚠️ Warning: Playlist '{candidate['name']}' latest track from "
                    f"{latest_track_year}, expected {year}"
                )
        return candidate

    # Multiple candidates - prefer the one with tracks from the target year.
    print(f"Found {len(candidates)} candidate playlists for {year}")
    if validate_with_tracks:
        for candidate in candidates:
            if get_latest_track_year(candidate["id"]) == year:
                print(f"✅ Selected '{candidate['name']}' (has tracks from {year})")
                return candidate

    print(f"Using first candidate: '{candidates[0]['name']}'")
    return candidates[0]


def find_playlist_by_year(
    year: int | None = None, validate_with_tracks: bool = True
) -> SearchResult:
    """
    Hardened search for a Fredagslistan playlist for a specific year.

    Paginates through the current user's playlists (with retry per page) and
    returns a tri-state result:

    - FOUND: a playlist whose name matches 'Fredagslistan YYYY' was found.
    - CONFIRMED_ABSENT: EVERY page was fetched successfully and none matched.
    - UNCERTAIN: a page ultimately failed, so absence cannot be proven. This
      must NEVER be treated as permission to create a new playlist.

    Args:
        year: The year to search for. Defaults to current year.
        validate_with_tracks: If True, use latest-track dates to disambiguate
            between multiple name matches (informational only).

    Returns:
        A :class:`SearchResult`.
    """
    if year is None:
        year = get_current_year()

    sp = get_spotify_client()

    candidates: list[dict] = []
    offset = 0
    limit = 50
    # Bound the walk so a pathological, never-terminating `next` cannot loop
    # forever; exceeding it means we could not prove completeness -> UNCERTAIN.
    max_pages = 200

    for _ in range(max_pages):
        results = _fetch_playlists_page(sp, limit, offset)
        if results is None:
            # A page ultimately failed: we cannot prove absence.
            return SearchResult(outcome=SearchOutcome.UNCERTAIN)
        if "items" not in results:
            # Malformed page (no items key): cannot prove the walk is complete.
            return SearchResult(outcome=SearchOutcome.UNCERTAIN)

        for playlist in results["items"]:
            if extract_year_from_playlist_name(playlist["name"]) == year:
                candidates.append(
                    {
                        "id": playlist["id"],
                        "name": playlist["name"],
                        "url": playlist["external_urls"]["spotify"],
                        "description": playlist.get("description", ""),
                        "track_count": playlist.get("tracks", {}).get("total"),
                    }
                )

        # Terminate ONLY when Spotify reports no next page. An empty INTERIOR
        # page (items=[] with a non-null next) must NOT end the walk, or a later
        # page could be missed and absence wrongly concluded.
        if results.get("next") is None:
            break
        offset += limit
    else:
        # Ran past the page cap without a terminating page: cannot prove absence.
        return SearchResult(outcome=SearchOutcome.UNCERTAIN)

    # Enumeration completed successfully here.
    if not candidates:
        return SearchResult(outcome=SearchOutcome.CONFIRMED_ABSENT)

    candidate = _select_candidate(candidates, year, validate_with_tracks)
    return SearchResult(outcome=SearchOutcome.FOUND, candidate=candidate)


def create_yearly_playlist(year: int | None = None) -> dict:
    """
    Create a new Fredagslistan playlist for a specific year.

    Args:
        year: The year for the playlist. Defaults to current year.

    Returns:
        Playlist dict with id, name, url, and description
    """
    if year is None:
        year = get_current_year()

    sp = get_spotify_client()
    user_id = _require(sp.current_user())["id"]

    name = generate_playlist_name(year)
    description = generate_playlist_description(year)

    print(f"Creating new playlist: {name}")

    playlist = _require(
        sp.user_playlist_create(
            user=user_id, name=name, public=True, collaborative=False, description=description
        )
    )

    print(f"Created playlist: {playlist['name']} ({playlist['id']})")
    print(f"URL: {playlist['external_urls']['spotify']}")

    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "url": playlist["external_urls"]["spotify"],
        "description": description,
    }


def _verify_cached_playlist(playlist_id: str, year: int) -> dict | None:
    """Verify a cached playlist id still exists, is accessible, and matches.

    Returns a playlist dict (including ``track_count``) if usable, else None
    (treated by the caller as a cache miss -> fall through to search).
    """
    sp = get_spotify_client()
    try:
        playlist = sp.playlist(playlist_id)
    except SpotifyException as exc:
        print(f"⚠️ Cached playlist {playlist_id} failed verification: {exc}")
        return None

    if playlist is None:
        print(f"⚠️ Cached playlist {playlist_id} returned no data")
        return None

    name = playlist.get("name", "")
    # Reject only if the name encodes a DIFFERENT year. A name that encodes no
    # year at all (e.g. someone renamed it and dropped the year) is still
    # trusted: we cached this id as the current year's playlist, so matching by
    # id avoids a spurious duplicate create on a harmless rename.
    name_year = extract_year_from_playlist_name(name)
    if name_year is not None and name_year != year:
        print(f"⚠️ Cached playlist name '{name}' now encodes {name_year}, not {year}")
        return None

    # Guard against a malformed response missing the fields we depend on.
    resolved_id = playlist.get("id")
    url = (playlist.get("external_urls") or {}).get("spotify")
    if not resolved_id or not url:
        print(f"⚠️ Cached playlist {playlist_id} missing id/url — treating as unverifiable")
        return None

    return {
        "id": resolved_id,
        "name": name,
        "url": url,
        "description": playlist.get("description", ""),
        "track_count": playlist.get("tracks", {}).get("total"),
    }


def _warn_if_playlist_empty(playlist: dict) -> None:
    """Non-destructive sanity check: warn (do not recreate) on 0 tracks.

    Only meaningful for a playlist we resolved to an EXISTING one; a freshly
    created playlist is expected to be empty and carries no ``track_count``.
    """
    count = playlist.get("track_count")
    if count == 0:
        print(
            f"⚠️ Anomaly: resolved playlist '{playlist['name']}' "
            f"({playlist['id']}) has 0 tracks — possible anomaly"
        )


def resolve_yearly_playlist(
    state: PlaylistState, year: int | None = None, dry_run: bool = False
) -> ResolutionResult:
    """Resolve the current-year playlist without ever creating on uncertainty.

    Algorithm:
      1. If the cached state is for the current year and its id verifies ->
         USED_CACHED (reset failures).
      2. Otherwise run the hardened search:
         - FOUND -> use it.
         - CONFIRMED_ABSENT -> create + (caller announces). In dry_run mode,
           no playlist is created; instead WOULD_CREATE is reported with no
           playlist, unchanged failures, and exit_code 0.
         - UNCERTAIN -> ABORTED: keep prior state, bump failure counter,
           never create.
      3. For an existing resolved playlist, warn (only) if it has 0 tracks.
    """
    if year is None:
        year = get_current_year()

    # 1. Cached happy path: verify without enumerating.
    if state.playlist_year == year and state.playlist_id:
        verified = _verify_cached_playlist(state.playlist_id, year)
        if verified is not None:
            print(f"✅ Using cached playlist: {verified['name']} ({verified['id']})")
            _warn_if_playlist_empty(verified)
            return success_result(state, PlaylistAction.USED_CACHED, verified, year)
        print("↩️ Cache miss — falling back to hardened search")

    # 2. Hardened search.
    search = find_playlist_by_year(year)

    if search.outcome is SearchOutcome.FOUND and search.candidate is not None:
        candidate = search.candidate
        print(f"✅ Found existing playlist via search: {candidate['name']} ({candidate['id']})")
        _warn_if_playlist_empty(candidate)
        return success_result(state, PlaylistAction.FOUND, candidate, year)

    if search.outcome is SearchOutcome.CONFIRMED_ABSENT:
        if dry_run:
            print(f"DRY RUN: would create a new Fredagslistan playlist for {year}")
            return ResolutionResult(
                action=PlaylistAction.WOULD_CREATE,
                playlist=None,
                playlist_id=state.playlist_id,
                playlist_year=state.playlist_year,
                search_failures=state.search_failures,
                failure_threshold=state.failure_threshold,
                was_created=False,
                exit_code=0,
            )
        print(f"No playlist for {year} (confirmed absent) — creating a new one")
        new_playlist = create_yearly_playlist(year)
        return success_result(state, PlaylistAction.CREATED, new_playlist, year, was_created=True)

    # UNCERTAIN: never create. Keep prior state, bump the failure counter.
    result = abort_result(state)
    print(
        f"⚠️ Playlist search UNCERTAIN — aborting (no create/announce). "
        f"failures={result.search_failures}/{result.failure_threshold}, "
        f"exit_code={result.exit_code}"
    )
    return result


def is_track_within_window(added_at: str, days_back: int = 6) -> bool:
    """
    Check if a track was added to the playlist within the rolling window.

    Args:
        added_at: ISO 8601 timestamp string (e.g., '2022-01-07T12:00:00Z')
        days_back: Number of days to look back (default: 6)

    Returns:
        True if the track was added within the last `days_back` days
    """
    # Parse the added_at timestamp (format: 2022-01-07T12:00:00Z) as UTC
    track_datetime = datetime.fromisoformat(added_at.replace("Z", "+00:00"))

    # Calculate the cutoff date (start of day, days_back days ago) in UTC
    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(days=days_back)
    cutoff_start_of_day = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)

    return track_datetime >= cutoff_start_of_day


def get_playlist(playlist_id: str, days_back: int = 6) -> list[dict]:
    """
    Get tracks added to the Spotify playlist within the rolling window.

    Only returns tracks added in the last `days_back` days. This allows
    songs that were added more than 6 days ago to "come back" if someone
    shares them again in Slack.

    Args:
        playlist_id: Spotify playlist ID
        days_back: Number of days to look back (default: 6)

    Returns:
        List of track dicts with name, url, and track_id
    """
    sp = get_spotify_client()

    playlist = _require(sp.playlist(playlist_id))
    print(playlist["name"])
    print(playlist["description"])
    print(playlist["external_urls"])

    # Get tracks added within the rolling window
    recent_songs = []

    results = playlist["tracks"]
    while results:
        for item in results["items"]:
            # Only include tracks added within the rolling window
            if is_track_within_window(item["added_at"], days_back):
                recent_songs.append(
                    {
                        "name": item["track"]["name"],
                        "url": item["track"]["external_urls"]["spotify"],
                        "track_id": item["track"]["id"],
                    }
                )

        if results["next"] is None:
            break

        try:
            results = sp.next(results)
        except SpotifyException:
            results = None

    return recent_songs


# Add tracks to playlist using track id
def add_songs_to_spotify_playlist(
    playlist_id: str, track_ids: str | list[str] | None = None
) -> None:
    sp = get_spotify_client()

    # make sure the incoming tracks is a list with strings
    if track_ids is None:
        track_ids = []
    elif not isinstance(track_ids, list):
        track_ids = [track_ids]

    if track_ids:
        # print('Adding tracks: ', track_ids)
        sp.playlist_add_items(playlist_id, track_ids)
    else:
        print("No tracks to add to playlist.")


def get_playlist_stats(playlist_id: str) -> dict:
    """
    Get statistics for a playlist including track count, top artists, and top genres.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        Dict with track_count, top_artists, and top_genres
    """
    sp = get_spotify_client()

    # Get all tracks from the playlist
    all_tracks = []
    artist_ids = []
    artist_counts = Counter()

    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results["items"]:
            if item["track"] is None:
                continue  # Skip deleted/unavailable tracks

            track = item["track"]
            all_tracks.append(track)

            # Count artist appearances
            for artist in track.get("artists", []):
                artist_counts[artist["name"]] += 1
                if artist.get("id"):
                    artist_ids.append(artist["id"])

        if results.get("next") is None:
            break

        try:
            results = sp.next(results)
        except SpotifyException:
            break

    # Get top artists
    top_artists = [artist for artist, _ in artist_counts.most_common(10)]

    # Get genres from artists (Spotify tracks don't have genres, artists do)
    genre_counts = Counter()

    # Fetch artist details in batches of 50 (Spotify API limit)
    unique_artist_ids = list(set(artist_ids))
    for i in range(0, len(unique_artist_ids), 50):
        batch = unique_artist_ids[i : i + 50]
        try:
            artists_data = _require(sp.artists(batch))
            for artist in artists_data.get("artists", []):
                if artist:
                    for genre in artist.get("genres", []):
                        genre_counts[genre] += 1
        except SpotifyException:
            continue

    top_genres = [genre for genre, _ in genre_counts.most_common(10)]

    return {
        "track_count": len(all_tracks),
        "top_artists": top_artists,
        "top_genres": top_genres,
    }


def get_previous_year_stats(year: int | None = None) -> dict | None:
    """
    Get stats from the previous year's playlist.

    Args:
        year: The current year (will get stats for year-1). Defaults to current year.

    Returns:
        Dict with track_count, top_artists, top_genres, and year, or None if no playlist found
    """
    if year is None:
        year = get_current_year()

    previous_year = year - 1

    # Find last year's playlist (informational stats only — any non-FOUND
    # outcome, including UNCERTAIN, simply yields no stats).
    search = find_playlist_by_year(previous_year)
    if search.outcome is not SearchOutcome.FOUND or search.candidate is None:
        print(f"No playlist found for {previous_year} (outcome={search.outcome.value})")
        return None

    previous_playlist = search.candidate

    print(f"Getting stats for {previous_year} playlist: {previous_playlist['name']}")

    stats = get_playlist_stats(previous_playlist["id"])
    stats["year"] = previous_year
    stats["playlist_name"] = previous_playlist["name"]
    stats["playlist_url"] = previous_playlist["url"]

    return stats
