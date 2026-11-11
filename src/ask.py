from src.recommender import load_songs
from src.rag import retrieve_songs, generate_answer


def main() -> None:
    songs = load_songs("data/songs.csv")
    query = input("What kind of music do you want? ")

    found_songs = retrieve_songs(query, songs, k=5)
    print("\nSongs found:")
    for song in found_songs:
        print(f"- {song['title']} ({song['genre']}, {song['mood']})")

    print("\nGemini says:")
    print(generate_answer(query, found_songs))


if __name__ == "__main__":
    main()