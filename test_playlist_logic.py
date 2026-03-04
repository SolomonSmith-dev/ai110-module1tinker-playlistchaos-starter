import pytest
from playlist_logic import (
    DEFAULT_PROFILE,
    classify_song,
    compute_playlist_stats,
    lucky_pick,
    normalize_song,
    search_songs,
    build_playlists,
    random_choice_or_none,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_profile():
    return dict(DEFAULT_PROFILE)  # hype_min=7, chill_max=3, favorite_genre=rock


@pytest.fixture
def sample_songs():
    return [
        {"title": "Thunderstruck", "artist": "AC/DC", "genre": "rock", "energy": 9, "tags": []},
        {"title": "Lo-fi Rain", "artist": "DJ Calm", "genre": "lofi", "energy": 2, "tags": []},
        {"title": "Night Drive", "artist": "Neon Echo", "genre": "electronic", "energy": 6, "tags": []},
        {"title": "Soft Piano", "artist": "Sleep Sound", "genre": "ambient", "energy": 1, "tags": []},
        {"title": "Sandstorm", "artist": "Darude", "genre": "electronic", "energy": 10, "tags": []},
    ]


# ---------------------------------------------------------------------------
# classify_song
# ---------------------------------------------------------------------------

class TestClassifySong:
    def test_high_energy_is_hype(self, default_profile):
        song = {"title": "Banger", "artist": "X", "genre": "pop", "energy": 8}
        assert classify_song(song, default_profile) == "Hype"

    def test_energy_at_hype_threshold_is_hype(self, default_profile):
        song = {"title": "Edge", "artist": "X", "genre": "pop", "energy": 7}
        assert classify_song(song, default_profile) == "Hype"

    def test_low_energy_is_chill(self, default_profile):
        song = {"title": "Quiet", "artist": "X", "genre": "pop", "energy": 2}
        assert classify_song(song, default_profile) == "Chill"

    def test_energy_at_chill_threshold_is_chill(self, default_profile):
        song = {"title": "Mellow", "artist": "X", "genre": "pop", "energy": 3}
        assert classify_song(song, default_profile) == "Chill"

    def test_favorite_genre_is_hype(self, default_profile):
        song = {"title": "Riff", "artist": "X", "genre": "rock", "energy": 5}
        assert classify_song(song, default_profile) == "Hype"

    def test_hype_genre_keyword_rock(self, default_profile):
        song = {"title": "Riff", "artist": "X", "genre": "rock", "energy": 5}
        assert classify_song(song, default_profile) == "Hype"

    def test_hype_genre_keyword_punk(self, default_profile):
        song = {"title": "Loud", "artist": "X", "genre": "punk", "energy": 5}
        assert classify_song(song, default_profile) == "Hype"

    def test_chill_title_keyword_lofi(self, default_profile):
        song = {"title": "lofi beats", "artist": "X", "genre": "pop", "energy": 8}
        assert classify_song(song, default_profile) == "Chill"

    def test_chill_title_keyword_sleep(self, default_profile):
        song = {"title": "sleep sounds", "artist": "X", "genre": "electronic", "energy": 9}
        assert classify_song(song, default_profile) == "Chill"

    def test_middle_energy_no_keywords_is_mixed(self, default_profile):
        song = {"title": "Normal Song", "artist": "X", "genre": "jazz", "energy": 5}
        assert classify_song(song, default_profile) == "Mixed"

    def test_chill_keyword_beats_hype_energy(self, default_profile):
        # Chill keyword should win over high energy — this was the original bug
        song = {"title": "ambient dreams", "artist": "X", "genre": "pop", "energy": 10}
        assert classify_song(song, default_profile) == "Chill"


# ---------------------------------------------------------------------------
# search_songs
# ---------------------------------------------------------------------------

class TestSearchSongs:
    def test_partial_match(self, sample_songs):
        results = search_songs(sample_songs, "AC", field="artist")
        titles = [s["title"] for s in results]
        assert "Thunderstruck" in titles

    def test_case_insensitive(self, sample_songs):
        results = search_songs(sample_songs, "ac/dc", field="artist")
        assert len(results) == 1
        assert results[0]["title"] == "Thunderstruck"

    def test_empty_query_returns_all(self, sample_songs):
        results = search_songs(sample_songs, "")
        assert len(results) == len(sample_songs)

    def test_no_match_returns_empty(self, sample_songs):
        results = search_songs(sample_songs, "zzznomatch", field="artist")
        assert results == []

    def test_search_by_title(self, sample_songs):
        results = search_songs(sample_songs, "lofi", field="title")
        assert len(results) == 1
        assert results[0]["artist"] == "DJ Calm"


# ---------------------------------------------------------------------------
# compute_playlist_stats
# ---------------------------------------------------------------------------

class TestComputePlaylistStats:
    def test_total_songs_counts_all(self, sample_songs, default_profile):
        playlists = build_playlists(sample_songs, default_profile)
        stats = compute_playlist_stats(playlists)
        assert stats["total_songs"] == len(sample_songs)

    def test_hype_ratio_is_fraction_of_total(self, sample_songs, default_profile):
        playlists = build_playlists(sample_songs, default_profile)
        stats = compute_playlist_stats(playlists)
        expected = stats["hype_count"] / stats["total_songs"]
        assert abs(stats["hype_ratio"] - expected) < 0.001

    def test_avg_energy_uses_all_songs(self, default_profile):
        songs = [
            {"title": "A", "artist": "X", "genre": "pop", "energy": 2, "tags": []},
            {"title": "B", "artist": "X", "genre": "pop", "energy": 8, "tags": []},
        ]
        playlists = build_playlists(songs, default_profile)
        stats = compute_playlist_stats(playlists)
        assert abs(stats["avg_energy"] - 5.0) < 0.001

    def test_empty_playlists(self):
        stats = compute_playlist_stats({"Hype": [], "Chill": [], "Mixed": []})
        assert stats["total_songs"] == 0
        assert stats["hype_ratio"] == 0.0
        assert stats["avg_energy"] == 0.0


# ---------------------------------------------------------------------------
# lucky_pick
# ---------------------------------------------------------------------------

class TestLuckyPick:
    def test_hype_mode_only_returns_hype(self, sample_songs, default_profile):
        playlists = build_playlists(sample_songs, default_profile)
        for _ in range(20):
            pick = lucky_pick(playlists, mode="hype")
            if pick is not None:
                assert pick["mood"] == "Hype"

    def test_chill_mode_only_returns_chill(self, sample_songs, default_profile):
        playlists = build_playlists(sample_songs, default_profile)
        for _ in range(20):
            pick = lucky_pick(playlists, mode="chill")
            if pick is not None:
                assert pick["mood"] == "Chill"

    def test_empty_playlist_returns_none(self):
        pick = lucky_pick({"Hype": [], "Chill": [], "Mixed": []}, mode="hype")
        assert pick is None

    def test_any_mode_can_return_mixed(self, default_profile):
        # Force a song into Mixed and verify any mode can pick it
        songs = [{"title": "Mid", "artist": "X", "genre": "jazz", "energy": 5, "tags": []}]
        playlists = build_playlists(songs, default_profile)
        picks = [lucky_pick(playlists, mode="any") for _ in range(30)]
        moods = {p["mood"] for p in picks if p is not None}
        assert "Mixed" in moods


# ---------------------------------------------------------------------------
# normalize_song
# ---------------------------------------------------------------------------

class TestNormalizeSong:
    def test_strips_whitespace(self):
        song = {"title": "  Hello  ", "artist": "  World  ", "genre": "  Pop  ", "energy": 5}
        result = normalize_song(song)
        assert result["title"] == "Hello"
        assert result["artist"] == "World"
        assert result["genre"] == "pop"

    def test_genre_lowercased(self):
        song = {"title": "X", "artist": "X", "genre": "ROCK", "energy": 5}
        result = normalize_song(song)
        assert result["genre"] == "rock"

    def test_artist_preserves_case(self):
        song = {"title": "X", "artist": "AC/DC", "genre": "rock", "energy": 5}
        result = normalize_song(song)
        assert result["artist"] == "AC/DC"

    def test_invalid_energy_defaults_to_zero(self):
        song = {"title": "X", "artist": "X", "genre": "pop", "energy": "bad"}
        result = normalize_song(song)
        assert result["energy"] == 0

    def test_tags_string_becomes_list(self):
        song = {"title": "X", "artist": "X", "genre": "pop", "energy": 5, "tags": "rock"}
        result = normalize_song(song)
        assert isinstance(result["tags"], list)


# ---------------------------------------------------------------------------
# random_choice_or_none
# ---------------------------------------------------------------------------

class TestRandomChoiceOrNone:
    def test_empty_list_returns_none(self):
        assert random_choice_or_none([]) is None

    def test_nonempty_list_returns_item(self):
        songs = [{"title": "A"}, {"title": "B"}]
        result = random_choice_or_none(songs)
        assert result in songs
