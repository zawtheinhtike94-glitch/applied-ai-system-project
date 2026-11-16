"""Evaluation script: run the agent on fixed requests and print a pass/fail summary."""
import contextlib
import io

from src.agent import run_agent
from src.guardrails import check_query
from src.recommender import load_songs

# Each case: a request, plus what a good top song should look like.
TEST_CASES = [
    {"query": "chill lofi for studying on a rainy night", "expect_genre": "lofi"},
    {"query": "songs for the gym", "expect_energy_above": 0.8},
    {"query": "bachata vibes for a date night", "expect_mood": "romantic"},
    {"query": "something sad and quiet for a breakup", "expect_mood": "sad"},
    {"query": "angry heavy music to scream to", "expect_genre": "metal"},
    {"query": "peaceful classical piano to fall asleep", "expect_genre": "classical"},
]

GUARDRAIL_CASES = ["", "     ", "a" * 500]


def check_case(case: dict, top_song: dict) -> bool:
    """Does the top song match what we expected for this request?"""
    if "expect_genre" in case and top_song["genre"] != case["expect_genre"]:
        return False
    if "expect_mood" in case and top_song["mood"] != case["expect_mood"]:
        return False
    if "expect_energy_above" in case and top_song["energy"] <= case["expect_energy_above"]:
        return False
    return True


def main() -> None:
    songs = load_songs("data/songs.csv")
    passed = 0

    print("=== Agent evaluation ===")
    for case in TEST_CASES:
        # Hide the agent's step-by-step printing so the summary stays short.
        with contextlib.redirect_stdout(io.StringIO()):
            results = run_agent(case["query"], songs)
        top_song, top_score, _ = results[0]
        ok = check_case(case, top_song)
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['query']!r} -> {top_song['title']} "
              f"({top_song['genre']}, {top_song['mood']}) score {top_score:.2f}")

    print("\n=== Guardrail evaluation ===")
    for query in GUARDRAIL_CASES:
        blocked = check_query(query) is not None
        passed += blocked
        status = "PASS" if blocked else "FAIL"
        label = repr(query) if len(query) < 20 else f"'{query[:10]}...' ({len(query)} chars)"
        print(f"[{status}] {label} blocked: {blocked}")

    total = len(TEST_CASES) + len(GUARDRAIL_CASES)
    print(f"\nSummary: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()