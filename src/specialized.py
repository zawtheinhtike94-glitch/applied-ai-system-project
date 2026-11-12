import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.rag import song_to_text

load_dotenv()  # reads GEMINI_API_KEY from .env

MODEL = "gemini-flash-lite-latest"

# The "personality" we give Gemini: a radio DJ with strict rules.
DJ_RULES = (
    "You are DJ Vibe, an upbeat late-night radio DJ.\n"
    "Rules:\n"
    "1. Start with a one-line radio intro that mentions the listener's request.\n"
    "2. Recommend exactly 3 songs, ONLY from the given list.\n"
    "3. Format each song as: 🎵 Title - Artist | why it fits (max 12 words)\n"
    "4. End with a one-line sign-off that starts with 'Stay tuned'.\n"
    "5. Never mention songs that are not in the list."
)

# Few-shot example: show Gemini exactly what a good answer looks like.
EXAMPLES = """Example request: something happy for a road trip
Example songs:
- Sunrise City by Neon Echo (pop, happy, energy 0.82)
- Rooftop Lights by Indigo Parade (indie pop, happy, energy 0.76)
- Island Sunday by Roots Harbor (reggae, laid-back, energy 0.48)
Example answer:
You're tuned in to DJ Vibe, and this one's for the road trippers out there!
🎵 Sunrise City - Neon Echo | bright, bouncy pop made for open highways
🎵 Rooftop Lights - Indigo Parade | sunny indie hooks to sing along with
🎵 Island Sunday - Roots Harbor | easy reggae groove for the slower miles
Stay tuned, and keep those windows down!"""


def generate_dj_answer(query: str, found_songs: List[Dict]) -> str:
    """Specialized version of generate_answer: same songs, DJ style and fixed format."""
    song_list = "\n".join(song_to_text(song) for song in found_songs)
    prompt = (
        f"{EXAMPLES}\n\n" 
        f"Now your turn.\nRequest: {query}\nSongs:\n{song_list}\nAnswer:"
    )
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=DJ_RULES),
    )
    return response.text