# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately rather than opening a public
issue:

- Use GitHub's **[Report a vulnerability](../../security/advisories/new)**
  (Security → Advisories) to open a private advisory, **or**
- email the maintainer at `david.lowelarsson@ur.se`.

You'll get an acknowledgement within a few days. Please include steps to
reproduce and the affected version/commit.

## Secrets & credentials

- No secrets are stored in this repository. All credentials
  (`SLACK_API_TOKEN`, `SPOTIPY_CLIENT_ID`/`_SECRET`/`_REDIRECT_URI`,
  `SPOTIPY_REFRESH_TOKEN`) live only in **GitHub Actions secrets**; locally they
  live in an untracked `.env`.
- The Spotify OAuth token cache (`.cache`) is gitignored and must never be
  committed. See the README "Spotify auth & token rotation" section for how to
  rotate the Spotify token if one is ever exposed.

## Scope

This is a small personal automation (Slack → Spotify playlist sync). It has no
public-facing runtime surface; the only external inputs are Slack messages in
the configured channel and the Spotify/Slack APIs.
