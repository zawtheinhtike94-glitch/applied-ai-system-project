import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads GEMINI_API_KEY from .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents="Say hello in one short sentence.",
)
print(response.text)
