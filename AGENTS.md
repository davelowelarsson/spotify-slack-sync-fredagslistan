# Agent & contributor guide — spotify-slack-sync-fredagslistan

Syncs Spotify tracks shared in a Slack channel (`#fredagslistan`) into a yearly
collaborative playlist. Runs headless on GitHub Actions (Fridays) and can be run
locally.

## What one run does

1. Resolve the current year's playlist from durable state (never creating on
   uncertainty — see the invariant below).
2. Read recent Slack messages (last 6 days, incl. thread replies) and extract
   Spotify track IDs.
3. Diff against the playlist's recent tracks and append the ones missing.
4. On a brand-new playlist only: announce it in Slack (Block Kit) + set the
   channel topic, with previous-year stats.

### 6-day rolling window

Both the Slack scan and the Spotify "already there?" check use a 6-day window.
It skips last Friday (7+ days) to avoid re-adding within the same week, and lets
a song "come back" if it's shared again months later.

## Tech stack & tooling

- Python 3.13, managed entirely by **uv** (`uv sync`, `uv run …`).
- **ruff** (lint + format) and **pyright** (basic) — config in `pyproject.toml`.
- `spotipy`, `slack_sdk`, `python-dotenv`; `pytest` + `freezegun` for tests.

```sh
uv sync                     # install (creates venv, fetches Python)
uv run python main.py       # run the sync locally
uv run pytest -q            # tests
uv run ruff check && uv run ruff format --check && uv run pyright
```

## Layout

```text
main.py                         # entry point: resolve → sync → emit state
utils/
  playlist_state.py             # PURE state: env in, GITHUB_OUTPUT out (no network)
  spotify_util.py               # Spotify: playlist resolution, search, stats
  spotify_access_token.py       # Spotify OAuth (refresh-token secret / local cache)
  slack_util.py                 # Slack: fetch tracks, announce, topic
  texts.py                      # rotating text templates
scripts/wrapped_stats.py        # read-only aggregate stats (for write-ups)
tests/                          # pytest suite (mocked APIs, freezegun)
.github/workflows/              # main.yml (sync), test.yml (quality), dependabot-automerge.yml
pyproject.toml / uv.lock        # deps + ruff/pyright config
```

## Architecture that matters

### ⚠️ Invariant: never create/announce on uncertainty

`create_yearly_playlist` + `announce_new_playlist` may fire **only** when the
playlist search returns `CONFIRMED_ABSENT` (a fully successful enumeration that
found no match). A transient/incomplete search once caused a duplicate playlist
+ a production announcement mid-year — do not regress this.

`spotify_util.find_playlist_by_year()` returns a tri-state `SearchResult`:
`FOUND` / `CONFIRMED_ABSENT` / `UNCERTAIN`. Any API error or incomplete
enumeration ⇒ `UNCERTAIN`, and `resolve_yearly_playlist()` then **aborts** (keeps
prior state, bumps a failure counter) — it never creates. A cache miss is never
permission to create.

### Durable state (Option B: workflow persists, app stays pure)

`utils/playlist_state.py` is network-free. The app **reads** state from env vars
and **emits** new values to `$GITHUB_OUTPUT`; the workflow persists them via
`gh variable set`. The app never calls the GitHub API.

- Repo **variables**: `FREDAGSLISTAN_PLAYLIST_ID`, `_PLAYLIST_YEAR`,
  `_SEARCH_FAILURES` (+ optional `_FAILURE_THRESHOLD`, default 5).
- On year rollover the cached id is ignored and a fresh playlist is resolved.
- When the failure counter hits the threshold, `main.py` emits a non-zero
  `exit_code` (as output, not a crash) so the workflow reddens the build *after*
  persisting the counter.
- Persisting needs a fine-grained PAT `GH_STATE_TOKEN` (single-repo,
  Variables:write). Without it the sync still runs; it just won't remember state.

### Dry-run

`DRY_RUN=1` (set on `push` events) does the full fetch/diff but makes **zero**
writes — no create, announce, topic, or track adds. Scheduled + `workflow_dispatch`
runs are real.

### Auth

`spotify_access_token.get_spotify_client()` authenticates from
`SPOTIPY_REFRESH_TOKEN` (a secret) held in memory — no committed token file. With
no refresh token it falls back to the local `.cache` / interactive OAuth (and
fails fast in CI). Local OAuth uses a loopback redirect `http://127.0.0.1:8888/callback`
(register it in the Spotify app; `localhost` is rejected). See the README for the
rotation runbook.

## Coding standards

- Type hints on public functions; let ruff (`E,W,F,I,UP,B,SIM,RUF,ARG,S110,S112`)
  and pyright basic guide the rest. No `# noqa` without reason. Line length 99.
- Small, single-purpose functions; comments for the non-obvious only.
- TDD: mock the Slack/Spotify clients, use `freezegun` for date logic,
  Arrange–Act–Assert. Every gate (ruff, format, pyright, pytest) stays green.
- Timezone: always UTC-aware (`datetime.now(tz=UTC)`).

## Environment

Local `.env` (see `.env.example`); GitHub **secrets** for CI:

```bash
SLACK_API_TOKEN           # Slack bot token (channels:history, chat:write, channels:manage, users:read)
SPOTIPY_CLIENT_ID         # Spotify app
SPOTIPY_CLIENT_SECRET
SPOTIPY_REDIRECT_URI      # http://127.0.0.1:8888/callback
SPOTIPY_REFRESH_TOKEN     # headless auth (see README rotation runbook)
SLACK_CHANNEL_ID          # optional; defaults to the production channel
```

## Gotchas

- Multiple links per message: use `re.findall` (not `search`). Track-ID regex:
  `open\.spotify\.com/track/(?:[A-Z]{2}/)?([a-zA-Z0-9]+)` (handles country codes
  + query params).
- Threads: check `reply_count`, fetch with `conversations_replies`.
- spotipy responses are typed `Optional`; use the `_require()` helper in
  `spotify_util` to fail loudly instead of a `NoneType` crash.
- `get_year_contributors` scans a whole year of Slack history — many API calls;
  use sparingly (yearly stats only).
