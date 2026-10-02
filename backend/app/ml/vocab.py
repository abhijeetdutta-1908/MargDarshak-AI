"""Maps the planner's interest / destination-type vocabulary onto dataset tags.

A destination tagged `forts` should satisfy a user interested in `history`, so matching
happens on these expanded tag sets rather than on exact words.
"""

INTEREST_TAGS: dict[str, set[str]] = {
    "trekking": {"trekking", "hiking", "mountains", "hills", "camping"},
    "photography": {"photography", "viewpoint", "sunrise", "sunset", "lakes", "architecture"},
    "food": {"food", "street-food", "cafes", "biryani", "seafood", "thali", "sweets", "bakery"},
    "shopping": {"shopping", "handicrafts", "textiles", "jewellery", "silk", "pashmina", "market"},
    "adventure": {
        "adventure", "rafting", "paragliding", "scuba", "snorkelling", "water-sports", "biking",
        "skiing", "bouldering", "camel-safari", "snow",
    },
    "nature": {
        "nature", "hills", "lakes", "gardens", "waterfalls", "backwaters", "tea", "coffee",
        "jungle", "river", "birding",
    },
    "history": {
        "history", "monuments", "forts", "palaces", "ruins", "unesco", "museum", "museums",
        "heritage", "colonial", "caves",
    },
    "culture": {
        "culture", "art", "dance", "music", "temple", "temples", "monastery", "monasteries",
        "handicrafts", "french-quarter", "ghats",
    },
    "nightlife": {"nightlife", "music", "bars"},
    "relaxation": {"relaxation", "beach", "yoga", "meditation", "houseboat", "romantic", "spa"},
    "wildlife": {"wildlife", "safari", "tiger-safari", "rhino", "birding", "zoo"},
}

TYPE_TAGS: dict[str, set[str]] = {
    "beach": {"beach"},
    "mountain": {"mountains", "hills", "snow"},
    "historical": {"history", "forts", "monuments", "ruins", "unesco"},
    "religious": {"spiritual", "temple", "temples", "ghats", "buddhism"},
    "adventure": {"adventure", "trekking", "rafting", "paragliding", "scuba", "biking"},
    "wildlife": {"wildlife", "safari", "tiger-safari", "rhino"},
    "city": {"city", "nightlife", "museums"},
    "nature": {"nature", "lakes", "tea", "backwaters", "waterfalls", "gardens"},
    "cultural": {"culture", "art", "palaces", "dance"},
}

# Activities that need dry weather; used by the itinerary's weather logic.
OUTDOOR_TAGS = {
    "trekking", "beach", "adventure", "rafting", "paragliding", "snorkelling", "scuba", "safari",
    "tiger-safari", "boating", "camel-safari", "viewpoint", "sunrise", "sunset", "waterfalls", "snow",
    "skiing", "kayaking", "cycling",
}


def interest_matches(interest: str, tags: set[str]) -> bool:
    return bool(INTEREST_TAGS.get(interest, {interest}) & tags) or interest in tags
