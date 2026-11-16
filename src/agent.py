import json
import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.guardrails import logger, safe_ai_call
from src.rag import retrieve_songs
from src.recommender import recommend_songs
from src.specialized import generate_dj_answer

load_dotenv()  # reads GEMINI_API_KEY from .env

MODEL = "gemini-flash-lite-latest"
GOOD_SCORE = 3.0  # top song must match genre AND mood to count as a good result


def plan_profile(query: str, songs: List[Dict], feedback: str = "") -> Dict:
    """Step 1 (PLAN): ask Gemini to turn a sentence into a listener profile."""
    genres = sorted({song["genre"] for song in songs})
    moods = sorted({song["mood"] for song in songs})
    prompt = (
        "Turn the user's music request into a listener profile.\n"
        f"Request: {query}\n\n"
        f"Pick favorite_genre from: {', '.join(genres)}\n"
        f"Pick favorite_mood from: {', '.join(moods)}\n"
        "Pick target_energy from 0.0 (very calm) to 1.0 (very loud).\n"
        'Reply with JSON only, like {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.3}'
        f"{feedback}"
    )
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


def check_results(results: List) -> bool:
    """Step 3 (CHECK): is the best song a strong match?"""
    best_score = results[0][1]
    return best_score >= GOOD_SCORE


def run_agent(query: str, songs: List[Dict], max_tries: int = 2) -> List:
    """Run the agent step by step and print what it does."""
    combos = sorted({f"{song['genre']}/{song['mood']}" for song in songs})
    feedback = ""
    best_results = None
    for attempt in range(1, max_tries + 1):
        print(f"--- Attempt {attempt} ---")
        print("Step 1 - PLAN: turning your request into a profile...")
        profile = safe_ai_call(plan_profile, query, songs, feedback, fallback=None)
        if profile is None:
            # Guardrail: Gemini is not available, so use the simple word finder instead.
            print("   Gemini is not available right now, using the simple finder instead.")
            best_results = [(song, 0.0, "") for song in retrieve_songs(query, songs, k=5)]
            break
        print(f"   Profile: {profile}")
        logger.info("Attempt %d profile: %s", attempt, profile)

        print("Step 2 - USE TOOL: asking the recommender for songs...")
        results = recommend_songs(profile, songs, k=5)
        for song, score, _ in results:
            print(f"   {song['title']} ({song['genre']}, {song['mood']}) score {score:.2f}")
        # Keep the best attempt, not just the last one.
        if best_results is None or results[0][1] > best_results[0][1]:
            best_results = results

        print("Step 3 - CHECK: is the top song a strong match?")
        if check_results(results):
            print("   Yes! Good match found.")
            break
        print(f"   No. Best score {results[0][1]:.2f} is below {GOOD_SCORE}.")
        # Tell Gemini what went wrong so the next plan can be better.
        feedback = (
            f"\n\nYour last profile {profile} gave weak matches. "
            f"These genre/mood pairs really exist in the catalog: {', '.join(combos)}. "
            "Pick a pair from this list that best fits the request."
        )
    else:
        # Guardrail: be honest when no strong match was found.
        print("   Out of tries. Note: these are the closest songs I have, not a perfect match.")
        logger.warning("No strong match for request: %s", query)

    print("Step 4 - ANSWER: asking DJ Vibe to explain the songs...")
    found_songs = [song for song, _, _ in best_results]
    backup_answer = "Here are my picks:\n" + "\n".join(
        f"- {song['title']} by {song['artist']}" for song in found_songs[:3]
    )
    answer = safe_ai_call(generate_dj_answer, query, found_songs, fallback=backup_answer)
    print(f"\n{answer}")
    return best_results