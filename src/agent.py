import json
import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.recommender import recommend_songs
from src.rag import generate_answer

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
    for attempt in range(1, max_tries + 1):
        print(f"--- Attempt {attempt} ---")
        print("Step 1 - PLAN: turning your request into a profile...")
        profile = plan_profile(query, songs, feedback)
        print(f"   Profile: {profile}")

        print("Step 2 - USE TOOL: asking the recommender for songs...")
        results = recommend_songs(profile, songs, k=5)
        for song, score, _ in results:
            print(f"   {song['title']} ({song['genre']}, {song['mood']}) score {score:.2f}")

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
        print("   Out of tries, using the best results I have.")

    print("Step 4 - ANSWER: asking Gemini to explain the songs...")
    found_songs = [song for song, _, _ in results]
    answer = generate_answer(query, found_songs)
    print(f"\n{answer}")
    return results