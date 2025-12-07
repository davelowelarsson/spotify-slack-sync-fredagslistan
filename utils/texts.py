"""
Rotating text templates for Fredagslistan.

This module contains all the fun, dynamic text templates used throughout
the application for playlist names, descriptions, Slack topics, and announcements.
All templates support {year} and {url} placeholders where applicable.
"""
from __future__ import annotations

import random
from typing import Optional


# =============================================================================
# PLAYLIST NAME TEMPLATES
# =============================================================================
# Format: Must contain "Fredagslistan" and {year} for identification
# The year is used for matching, so it must be in a consistent position

PLAYLIST_NAME_TEMPLATES = [
    "Fredagslistan {year} 🎵",
    "Fredagslistan {year} 🔥",
    "Fredagslistan {year} ✨",
    "Fredagslistan {year} 🚀",
    "Fredagslistan {year} 🎸",
    "Fredagslistan {year} 💃",
    "Fredagslistan {year} 🎧",
    "Fredagslistan {year} 🌟",
    "Fredagslistan {year} 🎶",
    "Fredagslistan {year} 🎤",
]

# Pattern for matching playlist names
# Matches both new format "Fredagslistan 2025 🎵" and old format "Fredagslistan ! 2024-25 !"
# First pattern: Verify it starts with Fredagslistan
PLAYLIST_NAME_PREFIX_PATTERN = r'^Fredagslistan\s*!?\s*'
# Second pattern: Find all 4-digit years or 2-digit year suffixes (e.g., "2024-25" -> 2024, 25)
PLAYLIST_YEAR_PATTERN = r'(\d{4})(?:-(\d{2}))?'


# =============================================================================
# PLAYLIST DESCRIPTION TEMPLATES
# =============================================================================
# Fun descriptions for the Spotify playlist

PLAYLIST_DESCRIPTION_TEMPLATES = [
    "UR pepp {year} 🔥",
    "Fredagsmusik från gänget {year} 🎵",
    "Årets fredagsbangers {year} 💪",
    "Varje fredag, varje vecka, hela {year} 🎧",
    "Musiken som fick oss genom {year} 🚀",
    "Fredagsfeeling {year} ✨",
    "Gängets spellistor {year} 🎶",
    "Fredagslåtar direkt från Slack {year} 💃",
    "Pepp och power {year} 🌟",
    "{year} års bästa fredagslåtar 🎸",
]


# =============================================================================
# SLACK CHANNEL TOPIC TEMPLATES
# =============================================================================
# Messages for the Slack channel topic (must include {url})

SLACK_TOPIC_TEMPLATES = [
    "🎵 Fredagslistan {year}: {url}",
    "🎧 Veckans musik finns här → {url}",
    "🌟 Fredagsvibes {year}! {url}",
    "🔥 Fredagslistan {year} är igång! {url}",
    "🎶 Här spelar vi {year}! {url}",
    "✨ Ny fredagslista! {url}",
    "{url}",  # Sometimes just the URL is fine
    "🚀 Fredagspepp {year}: {url}",
    "🎸 Rock on! Fredagslistan {year}: {url}",
    "💃 Dans in i helgen: {url}",
]


# =============================================================================
# ANNOUNCEMENT HEADER TEMPLATES
# =============================================================================
# Headers for the Slack announcement when a new playlist is created

ANNOUNCEMENT_HEADER_TEMPLATES = [
    "🎉 Ny Fredagslista för {year}!",
    "🚀 {year} års fredagslista är här!",
    "✨ Välkommen till Fredagslistan {year}!",
    "🔥 Dags för ny musik! Fredagslistan {year}",
    "🎵 Nytt år, ny spellista! {year}",
    "🎧 Fredagslistan {year} har landat!",
    "💃 Let's go! Fredagslistan {year}!",
    "🌟 {year} startar med ny fredagslista!",
    "🎸 Rock on! Ny lista för {year}!",
    "🎶 Musikåret {year} börjar här!",
]


# =============================================================================
# ANNOUNCEMENT BODY TEMPLATES
# =============================================================================
# Body text for the Slack announcement

ANNOUNCEMENT_BODY_TEMPLATES = [
    "En helt ny spellista har skapats för att samla årets fredagsmusik! 🎵",
    "Ny spellista redo för årets alla fredagslåtar! 🔥",
    "Dags att fylla på med musik! Dela låtar här så hamnar de i listan. 🎧",
    "Året har precis blivit lite bättre - ny fredagslista! ✨",
    "Spellistan är tom och väntar på era bästa låtar! 🚀",
    "En fräsch spellista för ett fräscht år! 💃",
    "Ladda upp med ny musik för fredagarna! 🎶",
    "Ny lista, nya möjligheter, samma fredagsfeeling! 🌟",
    "Redo för ännu ett år med grym fredagsmusik! 🎸",
    "Spellistan är skapad - nu är det upp till er! 🎤",
]


# =============================================================================
# STATS INTRO TEMPLATES
# =============================================================================
# Intro text when showing stats from the previous playlist
# These reference the playlist itself, not a specific time period

STATS_INTRO_TEMPLATES = [
    "📊 I {playlist_name} finns {track_count} låtar!",
    "🎵 {playlist_name} innehåller {track_count} fredagslåtar!",
    "✨ Hela {track_count} tracks i {playlist_name}!",
    "🔥 {track_count} låtar i {playlist_name}!",
    "🎧 {playlist_name} i siffror: {track_count} låtar!",
    "💪 {track_count} låtar har samlats i {playlist_name}!",
    "🚀 {playlist_name} har vuxit till {track_count} låtar!",
    "🎶 {playlist_name} = {track_count} fredagsbangers!",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_random_playlist_name(year: int) -> str:
    """Get a random playlist name with the year filled in."""
    template = random.choice(PLAYLIST_NAME_TEMPLATES)
    return template.format(year=year)


def get_random_playlist_description(year: int) -> str:
    """Get a random playlist description with the year filled in."""
    template = random.choice(PLAYLIST_DESCRIPTION_TEMPLATES)
    return template.format(year=year)


def get_random_topic_message(year: int, url: str) -> str:
    """Get a random topic message with year and URL filled in."""
    template = random.choice(SLACK_TOPIC_TEMPLATES)
    return template.format(year=year, url=url)


def get_random_announcement_header(year: int) -> str:
    """Get a random announcement header with the year filled in."""
    template = random.choice(ANNOUNCEMENT_HEADER_TEMPLATES)
    return template.format(year=year)


def get_random_announcement_body() -> str:
    """Get a random announcement body text."""
    return random.choice(ANNOUNCEMENT_BODY_TEMPLATES)


def get_random_stats_intro(playlist_name: str, track_count: int) -> str:
    """Get a random stats intro with playlist name and track count filled in."""
    template = random.choice(STATS_INTRO_TEMPLATES)
    return template.format(playlist_name=playlist_name, track_count=track_count)


def format_top_genres(genres: list[str], limit: int = 5) -> str:
    """
    Format a list of top genres into a readable string.
    
    Args:
        genres: List of genre names, ordered by popularity
        limit: Maximum number of genres to include
    
    Returns:
        Formatted string like "🎸 Rock • 🎵 Pop • 🎧 Electronic"
    """
    if not genres:
        return "Ingen genredata tillgänglig"
    
    # Genre emoji mapping
    genre_emojis = {
        'rock': '🎸',
        'pop': '🎵',
        'electronic': '🎧',
        'hip hop': '🎤',
        'rap': '🎤',
        'r&b': '💜',
        'soul': '💜',
        'jazz': '🎷',
        'classical': '🎻',
        'country': '🤠',
        'metal': '🤘',
        'punk': '🤘',
        'indie': '✨',
        'alternative': '✨',
        'dance': '💃',
        'reggae': '🌴',
        'blues': '🎺',
        'folk': '🪕',
        'latin': '💃',
        'k-pop': '🇰🇷',
        'swedish': '🇸🇪',
    }
    
    formatted = []
    for genre in genres[:limit]:
        genre_lower = genre.lower()
        # Find matching emoji
        emoji = '🎵'  # Default
        for key, value in genre_emojis.items():
            if key in genre_lower:
                emoji = value
                break
        formatted.append(f"{emoji} {genre.title()}")
    
    return " • ".join(formatted)


def format_top_artists(artists: list[str], limit: int = 5) -> str:
    """
    Format a list of top artists into a readable string.
    
    Args:
        artists: List of artist names, ordered by frequency
        limit: Maximum number of artists to include
    
    Returns:
        Formatted string like "1. Artist A • 2. Artist B • 3. Artist C"
    """
    if not artists:
        return "Ingen artistdata tillgänglig"
    
    formatted = [f"{i+1}. {artist}" for i, artist in enumerate(artists[:limit])]
    return " • ".join(formatted)


def format_top_contributors(contributors: list[dict], limit: int = 5) -> str:
    """
    Format a list of top contributors into a readable string.
    
    Args:
        contributors: List of dicts with 'user_name' and 'track_count' keys
        limit: Maximum number of contributors to include
    
    Returns:
        Formatted string like "🥇 Alice (42) • 🥈 Bob (38) • 🥉 Charlie (25)"
    """
    if not contributors:
        return "Ingen bidragsdata tillgänglig"
    
    # Medal emojis for top 3, then numbers
    medals = ['🥇', '🥈', '🥉', '4.', '5.', '6.', '7.', '8.', '9.', '10.']
    
    formatted = []
    for i, contributor in enumerate(contributors[:limit]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = contributor.get('user_name', 'Unknown')
        count = contributor.get('track_count', 0)
        formatted.append(f"{medal} {name} ({count})")
    
    return " • ".join(formatted)
