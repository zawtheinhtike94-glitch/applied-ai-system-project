import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads GEMINI_API_KEY from .env

MODEL = "gemini-flash-lite-latest"

# Words that hint the user wants calm or loud music.
LOW_ENERGY_WORDS = {"calm", "chill", "study", "studying", "sleep", "relax", "relaxing", "rainy", "quiet", "focus"}
HIGH_ENERGY_WORDS = {"gym", "workout", "party", "dance", "run", "running", "hype", "loud", "energetic"}


def retrieve_songs(query: str, songs: List[Dict], k: int = 5) -> List[Dict]:
    """Find the k songs that best match a plain-English request."""
    words = set(query.lower().replace(",", " ").split())

    def match_points(song: Dict) -> float:
        points = 0.0
        if song["genre"] in words:
            points += 2
        if song["mood"] in words:
            points += 1
        if words & LOW_ENERGY_WORDS:
            points += 1 - song["energy"]  # calmer song = more points
        if words & HIGH_ENERGY_WORDS:
            points += song["energy"]      # louder song = more points
        return points

    return sorted(songs, key=match_points, reverse=True)[:k]


def song_to_text(song: Dict) -> str:
    """Turn one song into a short line Gemini can read."""
    return f"- {song['title']} by {song['artist']} ({song['genre']}, {song['mood']}, energy {song['energy']})"


def generate_answer(query: str, found_songs: List[Dict]) -> str:
    """Ask Gemini to recommend songs, using ONLY the songs we found."""
    song_list = "\n".join(song_to_text(song) for song in found_songs)
    prompt = (
        "You are a friendly music assistant.\n"
        f"The user asked: {query}\n\n"
        "Recommend songs using ONLY this list. Do not invent other songs.\n"
        f"{song_list}\n\n"
        "Pick the best 3 and explain each in one short sentence."
    )
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text