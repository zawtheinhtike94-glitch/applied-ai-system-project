from src import agent
from src.guardrails import check_query, safe_ai_call
from src.rag import retrieve_songs
from src.recommender import load_songs

SONGS = load_songs("data/songs.csv")


# --- Guardrail tests ---

def test_empty_request_is_rejected():
    assert check_query("   ") is not None


def test_too_long_request_is_rejected():
    assert check_query("a" * 500) is not None


def test_normal_request_is_allowed():
    assert check_query("chill lofi for studying") is None


def test_safe_ai_call_returns_fallback_when_ai_fails():
    def broken_ai(query):
        raise RuntimeError("503 UNAVAILABLE")

    assert safe_ai_call(broken_ai, "hi", fallback="backup") == "backup"


# --- RAG finder tests ---

def test_finder_returns_calm_lofi_for_study_request():
    found = retrieve_songs("chill lofi for studying", SONGS, k=5)
    assert found[0]["genre"] == "lofi"
    assert all(song["energy"] < 0.5 for song in found[:3])


def test_finder_returns_loud_songs_for_gym_request():
    found = retrieve_songs("songs for the gym", SONGS, k=3)
    assert all(song["energy"] > 0.8 for song in found)


# --- Agent tests (fake Gemini, so they run without internet) ---

def test_agent_retries_after_weak_plan(monkeypatch):
    plans = iter([
        {"favorite_genre": "pop", "favorite_mood": "romantic", "target_energy": 0.6},  # weak
        {"favorite_genre": "r&b", "favorite_mood": "romantic", "target_energy": 0.6},  # strong
    ])
    monkeypatch.setattr(agent, "plan_profile", lambda *args: next(plans))
    monkeypatch.setattr(agent, "generate_dj_answer", lambda *args: "DJ answer")

    results = agent.run_agent("bachata vibes for a date night", SONGS)
    assert results[0][0]["title"] == "Velvet Midnight"


def test_agent_keeps_best_attempt_not_last(monkeypatch):
    plans = iter([
        {"favorite_genre": "pop", "favorite_mood": "romantic", "target_energy": 0.6},  # best score 2.78
        {"favorite_genre": "metal", "favorite_mood": "sad", "target_energy": 0.1},     # worse
    ])
    monkeypatch.setattr(agent, "plan_profile", lambda *args: next(plans))
    monkeypatch.setattr(agent, "generate_dj_answer", lambda *args: "DJ answer")

    results = agent.run_agent("bachata vibes for a date night", SONGS)
    assert results[0][0]["genre"] == "pop"


def test_agent_falls_back_to_finder_when_gemini_is_down(monkeypatch):
    def gemini_down(*args):
        raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(agent, "plan_profile", gemini_down)
    monkeypatch.setattr(agent, "generate_dj_answer", gemini_down)

    results = agent.run_agent("chill lofi for studying", SONGS)
    assert results[0][0]["genre"] == "lofi"