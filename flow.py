from pocketflow import Flow

from nodes import ParseInputNode, SearchRestaurantsNode, RankAndRecommendNode


def create_restaurant_flow() -> Flow:
    """Create and return the restaurant suggestion flow."""

    parse_node = ParseInputNode()
    search_node = SearchRestaurantsNode()
    rank_node = RankAndRecommendNode()

    # Linear router-worker style pipeline
    parse_node >> search_node
    search_node >> rank_node

    return Flow(start=parse_node)


restaurant_flow = create_restaurant_flow()