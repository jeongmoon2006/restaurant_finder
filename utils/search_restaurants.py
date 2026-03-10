import os
from typing import List, Dict, Optional

import requests


GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def search_restaurants(
    lat: float,
    lng: float,
    price_level: int,
    keyword: Optional[str] = None,
    radius_meters: int = 3000,
    max_results: int = 15,
) -> List[Dict]:
    """Search nearby restaurants using Google Places Text Search.

    Inputs
    ------
    lat, lng: coordinates of the search center
    price_level: 1-4 (Google's price_level semantics)
    keyword: optional free-text keyword (e.g., "romantic dinner", "kid friendly")
    radius_meters: search radius in meters
    max_results: maximum number of restaurants to return

    Output
    -------
    List of restaurant dicts with minimal normalized fields:
      - name
      - address
      - rating
      - price_level
      - description
      - reviews_snippet
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY environment variable is not set")

    params = {
        "key": api_key,
        "location": f"{lat},{lng}",
        "radius": radius_meters,
        "type": "restaurant",
    }

    # Clamp price_level to [1, 4]
    if price_level is not None:
        clamped = max(1, min(4, int(price_level)))
        params["maxprice"] = clamped

    if keyword:
        params["query"] = keyword
    else:
        params["query"] = "restaurant"

    resp = requests.get(GOOGLE_PLACES_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", [])[:max_results]:
        name = item.get("name", "")
        address = item.get("formatted_address") or item.get("vicinity", "")
        rating = item.get("rating")
        pl = item.get("price_level")
        # Use types or business_status as a lightweight description
        description = ", ".join(item.get("types", [])[:5]) or item.get("business_status", "")
        reviews_snippet = item.get("user_ratings_total")

        results.append(
            {
                "name": name,
                "address": address,
                "rating": rating,
                "price_level": pl,
                "description": description,
                "reviews_snippet": str(reviews_snippet) if reviews_snippet is not None else "",
            }
        )

    return results


if __name__ == "__main__":
    # Simple manual test stub
    # Make sure to set GOOGLE_MAPS_API_KEY before running.
    sample = search_restaurants(lat=37.7749, lng=-122.4194, price_level=2, keyword="brunch")
    for r in sample[:3]:
        print(r)
