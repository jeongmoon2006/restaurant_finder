from dotenv import load_dotenv

from flow import create_restaurant_flow


def main() -> None:
    """Run the Restaurant Suggestion Agent as a simple CLI app."""

    # Load environment variables (OPENAI_API_KEY, GOOGLE_MAPS_API_KEY, etc.)
    load_dotenv()

    print("Restaurant Suggestion Agent")
    print("Describe what you're looking for (location, budget, occasion).")
    user_query = input("> ")

    shared = {
        "user_query": user_query,
        "location_data": {},
        "price_level": None,
        "occasion_tags": [],
        "candidates_list": [],
        "final_recommendations": [],
    }

    flow = create_restaurant_flow()
    flow.run(shared)

    recommendations = shared.get("final_recommendations") or []
    if not recommendations:
        print("\nNo recommendations could be generated. Please try refining your query.")
        return

    print("\nTop restaurant recommendations:")
    for idx, rec in enumerate(recommendations, start=1):
        name = rec.get("name", "(unknown)")
        address = rec.get("address", "")
        rating = rec.get("rating")
        reason = rec.get("reason", "")
        rating_str = f" (rating: {rating})" if rating is not None else ""
        print(f"{idx}. {name}{rating_str}")
        if address:
            print(f"   Address: {address}")
        if reason:
            print(f"   Reason: {reason}")


if __name__ == "__main__":
    main()
