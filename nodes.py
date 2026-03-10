from typing import Any, Dict, List

import yaml
from pocketflow import Node

from utils.call_llm import call_llm
from utils.search_restaurants import search_restaurants


class ParseInputNode(Node):
    """Parse free-text user query into structured fields.

    Reads:
      - shared["user_query"]

    Writes:
      - shared["location_data"] (lat, lng, address_text)
      - shared["price_level"]
      - shared["occasion_tags"]
    """

    def prep(self, shared: Dict[str, Any]) -> str:
        return shared.get("user_query", "")

    def exec(self, user_query: str) -> Dict[str, Any]:
        # Single-line f-string to avoid nested triple-quotes problems
        prompt = (
            "You are a helpful assistant that extracts structured data from a "
            "restaurant search query.\n\n"
            f"User query:\n{user_query}\n\n"
            "Extract the following fields and output ONLY valid YAML:\n\n"
            "location_data:\n"
            "  lat: <float latitude>\n"
            "  lng: <float longitude>\n"
            "  address_text: <short human readable location>\n"
            "price_level: <integer 1-4 where 1=cheap and 4=luxury>\n"
            "occasion_tags:\n"
            "  - <tag1>\n"
            "  - <tag2>\n"
            "  - <tag3>\n"
        )

        response = call_llm(prompt)

        try:
            data = yaml.safe_load(response)
        except Exception as exc:  # Let Node retry on bad format
            raise ValueError("Failed to parse YAML from LLM response") from exc

        if not isinstance(data, dict):
            raise ValueError("Parsed YAML is not a dict")

        # Minimal validation
        if "location_data" not in data or "price_level" not in data:
            raise ValueError("Missing required fields in parsed data")

        loc = data["location_data"]
        if not isinstance(loc, dict) or "lat" not in loc or "lng" not in loc:
            raise ValueError("location_data must contain lat and lng")

        # Coerce types conservatively
        lat = float(loc["lat"])
        lng = float(loc["lng"])
        address_text = str(loc.get("address_text", ""))
        price_level = int(data["price_level"])
        price_level = max(1, min(4, price_level))
        occasion_tags = data.get("occasion_tags") or []
        if not isinstance(occasion_tags, list):
            occasion_tags = [str(occasion_tags)]
        occasion_tags = [str(t) for t in occasion_tags]

        return {
            "location_data": {
                "lat": lat,
                "lng": lng,
                "address_text": address_text,
            },
            "price_level": price_level,
            "occasion_tags": occasion_tags,
        }

    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> None:
        shared["location_data"] = exec_res["location_data"]
        shared["price_level"] = exec_res["price_level"]
        shared["occasion_tags"] = exec_res["occasion_tags"]


class SearchRestaurantsNode(Node):
    """Call external API to fetch restaurant candidates."""

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "location_data": shared.get("location_data", {}),
            "price_level": shared.get("price_level"),
            "occasion_tags": shared.get("occasion_tags", []),
        }

    def exec(self, prep_res: Dict[str, Any]) -> List[Dict[str, Any]]:
        location_data = prep_res["location_data"]
        lat = float(location_data["lat"])
        lng = float(location_data["lng"])
        price_level = prep_res["price_level"]
        tags = prep_res.get("occasion_tags") or []
        keyword = ", ".join(tags) if tags else None
        return search_restaurants(lat=lat, lng=lng, price_level=price_level, keyword=keyword)

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: List[Dict[str, Any]]) -> None:
        shared["candidates_list"] = exec_res


class RankAndRecommendNode(Node):
    """Rank restaurant candidates with the LLM and select top 3.

    Guardrail: the LLM must only choose from the provided candidates and
    must not invent new restaurant names.
    """

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_query": shared.get("user_query", ""),
            "occasion_tags": shared.get("occasion_tags", []),
            "candidates_list": shared.get("candidates_list", []),
        }

    def exec(self, prep_res: Dict[str, Any]) -> List[Dict[str, Any]]:
        user_query = prep_res["user_query"]
        occasion_tags = prep_res.get("occasion_tags") or []
        candidates: List[Dict[str, Any]] = prep_res.get("candidates_list") or []

        if not candidates:
            return []

        # Prepare a compact representation of candidates
        candidate_lines: List[str] = []
        candidate_names = set()
        for idx, c in enumerate(candidates, start=1):
            name = str(c.get("name", ""))
            candidate_names.add(name)
            address = c.get("address", "")
            rating = c.get("rating", "")
            price_level = c.get("price_level", "")
            description = c.get("description", "")
            candidate_lines.append(
                f"- id: {idx}\\n  name: {name}\\n  address: {address}\\n  rating: {rating}\\n  price_level: {price_level}\\n  description: {description}"
            )

        candidates_block = "\n".join(candidate_lines)
        tags_str = ", ".join(occasion_tags)

        prompt = (
            "You are a restaurant recommendation expert.\n\n"
            f"User query:\n{user_query}\n\n"
            f"Occasion / taste tags: {tags_str}\n\n"
            "Here is a list of candidate restaurants (YAML-like list):\n"
            f"{candidates_block}\n\n"
            "Now choose up to 3 restaurants that best match the user's intent.\n"
            "Return ONLY valid YAML in the following format:\n\n"
            "recommendations:\n"
            "  - name: <exact name from candidates>\n"
            "    address: <address>\n"
            "    rating: <numeric rating or null>\n"
            "    reason: <1-2 sentence reason tailored to the query>\n"
            "  - name: ...\n"
        )

        response = call_llm(prompt)

        try:
            data = yaml.safe_load(response)
        except Exception as exc:
            raise ValueError("Failed to parse YAML from LLM ranking response") from exc

        if not isinstance(data, dict) or "recommendations" not in data:
            raise ValueError("Missing 'recommendations' in LLM response")

        recs = data["recommendations"]
        if not isinstance(recs, list):
            raise ValueError("recommendations must be a list")

        # Validate guardrail: names must be subset of candidate_names
        validated: List[Dict[str, Any]] = []
        for rec in recs[:3]:
            if not isinstance(rec, dict) or "name" not in rec:
                continue
            name = str(rec["name"])
            if name not in candidate_names:
                raise ValueError(f"LLM tried to recommend unknown restaurant: {name}")
            # Look up rating/address from original candidates if missing
            base = next((c for c in candidates if str(c.get("name", "")) == name), {})
            address = rec.get("address") or base.get("address", "")
            rating = rec.get("rating") or base.get("rating")
            reason = rec.get("reason") or ""
            validated.append(
                {
                    "name": name,
                    "address": address,
                    "rating": rating,
                    "reason": reason,
                }
            )

        return validated

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: List[Dict[str, Any]]) -> None:
        shared["final_recommendations"] = exec_res
