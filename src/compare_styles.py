from src.recommender import load_songs
from src.rag import retrieve_songs, generate_answer
from src.specialized import generate_dj_answer


def main() -> None:
    songs = load_songs("data/songs.csv")
    query = "chill lofi for studying on a rainy night"
    found_songs = retrieve_songs(query, songs, k=5)

    print("=== NORMAL (baseline) ===")
    print(generate_answer(query, found_songs))

    print("\n=== SPECIALIZED (DJ Vibe) ===")
    print(generate_dj_answer(query, found_songs))


if __name__ == "__main__":
    main()