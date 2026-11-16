from src.agent import run_agent
from src.guardrails import check_query, logger
from src.recommender import load_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    query = input("What kind of music do you want? ")

    # Guardrail: stop bad input before calling Gemini.
    problem = check_query(query)
    if problem:
        print(problem)
        logger.warning("Rejected request: %r", query)
        return

    logger.info("New request: %s", query)
    run_agent(query, songs)


if __name__ == "__main__":
    main()