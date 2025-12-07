"""Tests for the texts utility module."""
import pytest
from utils.texts import (
    PLAYLIST_NAME_TEMPLATES,
    PLAYLIST_NAME_PREFIX_PATTERN,
    PLAYLIST_YEAR_PATTERN,
    PLAYLIST_DESCRIPTION_TEMPLATES,
    SLACK_TOPIC_TEMPLATES,
    ANNOUNCEMENT_HEADER_TEMPLATES,
    ANNOUNCEMENT_BODY_TEMPLATES,
    STATS_INTRO_TEMPLATES,
    get_random_playlist_name,
    get_random_playlist_description,
    get_random_topic_message,
    get_random_announcement_header,
    get_random_announcement_body,
    get_random_stats_intro,
    format_top_genres,
    format_top_artists,
)
from utils.spotify_util import extract_year_from_playlist_name
import re


class TestPlaylistNameTemplates:
    """Tests for playlist name generation."""
    
    def test_all_templates_contain_year_placeholder(self):
        """All playlist name templates should have {year} placeholder."""
        for template in PLAYLIST_NAME_TEMPLATES:
            assert "{year}" in template, f"Template missing {{year}}: {template}"
    
    def test_all_templates_contain_fredagslistan(self):
        """All playlist name templates should contain 'Fredagslistan'."""
        for template in PLAYLIST_NAME_TEMPLATES:
            assert "Fredagslistan" in template, f"Template missing 'Fredagslistan': {template}"
    
    def test_get_random_playlist_name_contains_year(self):
        """Generated playlist name should contain the year."""
        name = get_random_playlist_name(2025)
        assert "2025" in name
    
    def test_get_random_playlist_name_matches_pattern(self):
        """Generated playlist name should extract year correctly."""
        for _ in range(20):  # Test multiple random names
            name = get_random_playlist_name(2025)
            year = extract_year_from_playlist_name(name)
            assert year == 2025, f"Name doesn't extract year correctly: {name}"
    
    def test_templates_list_not_empty(self):
        """Template list should have entries."""
        assert len(PLAYLIST_NAME_TEMPLATES) >= 5


class TestPlaylistDescriptionTemplates:
    """Tests for playlist description generation."""
    
    def test_all_templates_contain_year_placeholder(self):
        """All description templates should have {year} placeholder."""
        for template in PLAYLIST_DESCRIPTION_TEMPLATES:
            assert "{year}" in template, f"Template missing {{year}}: {template}"
    
    def test_get_random_playlist_description_contains_year(self):
        """Generated description should contain the year."""
        desc = get_random_playlist_description(2025)
        assert "2025" in desc
    
    def test_templates_list_not_empty(self):
        """Template list should have entries."""
        assert len(PLAYLIST_DESCRIPTION_TEMPLATES) >= 5


class TestSlackTopicTemplates:
    """Tests for Slack topic message generation."""
    
    def test_all_templates_contain_url_placeholder(self):
        """All topic templates should have {url} placeholder."""
        for template in SLACK_TOPIC_TEMPLATES:
            assert "{url}" in template, f"Template missing {{url}}: {template}"
    
    def test_get_random_topic_message_contains_url(self):
        """Generated topic should contain the URL."""
        url = "https://open.spotify.com/playlist/test123"
        topic = get_random_topic_message(2025, url)
        assert url in topic
    
    def test_templates_list_not_empty(self):
        """Template list should have entries."""
        assert len(SLACK_TOPIC_TEMPLATES) >= 5


class TestAnnouncementTemplates:
    """Tests for announcement text generation."""
    
    def test_header_templates_contain_year_placeholder(self):
        """All header templates should have {year} placeholder."""
        for template in ANNOUNCEMENT_HEADER_TEMPLATES:
            assert "{year}" in template, f"Template missing {{year}}: {template}"
    
    def test_get_random_announcement_header_contains_year(self):
        """Generated header should contain the year."""
        header = get_random_announcement_header(2025)
        assert "2025" in header
    
    def test_get_random_announcement_body_not_empty(self):
        """Generated body should not be empty."""
        body = get_random_announcement_body()
        assert len(body) > 0
    
    def test_body_templates_list_not_empty(self):
        """Template list should have entries."""
        assert len(ANNOUNCEMENT_BODY_TEMPLATES) >= 5


class TestStatsTemplates:
    """Tests for stats intro generation."""
    
    def test_stats_intro_templates_have_placeholders(self):
        """All stats templates should have {playlist_name} and {track_count}."""
        for template in STATS_INTRO_TEMPLATES:
            assert "{playlist_name}" in template, f"Template missing {{playlist_name}}: {template}"
            assert "{track_count}" in template, f"Template missing {{track_count}}: {template}"
    
    def test_get_random_stats_intro_contains_values(self):
        """Generated stats intro should contain playlist name and track count."""
        intro = get_random_stats_intro("Fredagslistan 2024 🎵", 150)
        assert "Fredagslistan 2024" in intro
        assert "150" in intro


class TestFormatTopGenres:
    """Tests for genre formatting."""
    
    def test_format_empty_list(self):
        """Empty list should return a message."""
        result = format_top_genres([])
        assert "Ingen genredata" in result
    
    def test_format_single_genre(self):
        """Single genre should be formatted."""
        result = format_top_genres(["rock"])
        assert "Rock" in result
    
    def test_format_multiple_genres(self):
        """Multiple genres should be joined."""
        result = format_top_genres(["rock", "pop", "electronic"])
        assert "Rock" in result
        assert "Pop" in result
        assert "Electronic" in result
        assert "•" in result  # Check separator
    
    def test_respects_limit(self):
        """Should respect the limit parameter."""
        genres = ["rock", "pop", "electronic", "jazz", "blues", "country"]
        result = format_top_genres(genres, limit=3)
        # Should only have 3 genres (2 separators)
        assert result.count("•") == 2
    
    def test_adds_appropriate_emoji(self):
        """Should add appropriate emoji for known genres."""
        result = format_top_genres(["rock"])
        assert "🎸" in result
        
        result = format_top_genres(["hip hop"])
        assert "🎤" in result


class TestFormatTopArtists:
    """Tests for artist formatting."""
    
    def test_format_empty_list(self):
        """Empty list should return a message."""
        result = format_top_artists([])
        assert "Ingen artistdata" in result
    
    def test_format_single_artist(self):
        """Single artist should be formatted with number."""
        result = format_top_artists(["The Beatles"])
        assert "1. The Beatles" in result
    
    def test_format_multiple_artists(self):
        """Multiple artists should be numbered and joined."""
        result = format_top_artists(["Artist A", "Artist B", "Artist C"])
        assert "1. Artist A" in result
        assert "2. Artist B" in result
        assert "3. Artist C" in result
        assert "•" in result
    
    def test_respects_limit(self):
        """Should respect the limit parameter."""
        artists = ["A", "B", "C", "D", "E", "F"]
        result = format_top_artists(artists, limit=3)
        assert "1. A" in result
        assert "2. B" in result
        assert "3. C" in result
        assert "4." not in result


class TestFormatTopContributors:
    """Tests for contributor formatting."""
    
    def test_format_empty_list(self):
        """Empty list should return a message."""
        from utils.texts import format_top_contributors
        result = format_top_contributors([])
        assert "Ingen bidragsdata" in result
    
    def test_format_single_contributor(self):
        """Single contributor should get gold medal."""
        from utils.texts import format_top_contributors
        contributors = [{'user_name': 'Alice', 'track_count': 42}]
        result = format_top_contributors(contributors)
        assert "🥇" in result
        assert "Alice" in result
        assert "42" in result
    
    def test_format_top_three_with_medals(self):
        """Top 3 should have gold, silver, bronze medals."""
        from utils.texts import format_top_contributors
        contributors = [
            {'user_name': 'Alice', 'track_count': 42},
            {'user_name': 'Bob', 'track_count': 38},
            {'user_name': 'Charlie', 'track_count': 25},
        ]
        result = format_top_contributors(contributors)
        assert "🥇" in result
        assert "🥈" in result
        assert "🥉" in result
        assert "Alice (42)" in result
        assert "Bob (38)" in result
        assert "Charlie (25)" in result
    
    def test_format_more_than_three_uses_numbers(self):
        """4th and 5th should use numbers instead of medals."""
        from utils.texts import format_top_contributors
        contributors = [
            {'user_name': 'Alice', 'track_count': 42},
            {'user_name': 'Bob', 'track_count': 38},
            {'user_name': 'Charlie', 'track_count': 25},
            {'user_name': 'Diana', 'track_count': 20},
            {'user_name': 'Eve', 'track_count': 15},
        ]
        result = format_top_contributors(contributors)
        assert "4. Diana" in result
        assert "5. Eve" in result
    
    def test_respects_limit(self):
        """Should respect the limit parameter."""
        from utils.texts import format_top_contributors
        contributors = [
            {'user_name': f'User{i}', 'track_count': 10 - i}
            for i in range(10)
        ]
        result = format_top_contributors(contributors, limit=3)
        assert "User0" in result
        assert "User2" in result
        assert "User3" not in result
