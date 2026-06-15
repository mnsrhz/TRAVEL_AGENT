DEMO_DESTINATION_PLAN = {
    "title": "10-day Japan - Tokyo, Kyoto, Osaka",
    "cities": [
        {"city": "Tokyo", "days": 4, "rationale": "Arrival hub, neighborhoods, food, and museums."},
        {"city": "Kyoto", "days": 3, "rationale": "Temples, shrines, and traditional districts."},
        {"city": "Osaka", "days": 3, "rationale": "Food, day trips, and departure flexibility."},
    ],
    "source": "demo",
}

DEMO_FLIGHTS = [
    {
        "title": "SFO to Tokyo - ANA demo option",
        "airline": "ANA",
        "price": 820,
        "duration": "11h 20m",
        "source": "demo",
    }
]

DEMO_HOTELS = [
    {"name": "Shinjuku Granbell Hotel", "city": "Tokyo", "nightly_price": 140, "rating": 4.2, "source": "demo"},
    {"name": "Kyoto Granbell Hotel", "city": "Kyoto", "nightly_price": 130, "rating": 4.4, "source": "demo"},
    {"name": "Hotel The Flag Shinsaibashi", "city": "Osaka", "nightly_price": 120, "rating": 4.5, "source": "demo"},
]

DEMO_ATTRACTIONS = [
    {"name": "Senso-ji Temple", "city": "Tokyo", "duration_hours": 2, "source": "demo"},
    {"name": "Shibuya Crossing and Harajuku", "city": "Tokyo", "duration_hours": 3, "source": "demo"},
    {"name": "Fushimi Inari Taisha", "city": "Kyoto", "duration_hours": 3, "source": "demo"},
    {"name": "Dotonbori", "city": "Osaka", "duration_hours": 2, "source": "demo"},
]

DEMO_RESTAURANTS = [
    {"name": "Vegan Ramen UZU", "city": "Tokyo", "dietary": "vegetarian", "rating": 4.5, "source": "demo"},
    {"name": "TowZen", "city": "Kyoto", "dietary": "vegetarian", "rating": 4.6, "source": "demo"},
    {"name": "Paprika Shokudo", "city": "Osaka", "dietary": "vegetarian", "rating": 4.4, "source": "demo"},
]

DEMO_TRANSIT = [
    {"origin": "Shinjuku", "destination": "Asakusa", "duration_minutes": 35, "mode": "metro", "source": "demo"},
    {"origin": "Kyoto Station", "destination": "Fushimi Inari", "duration_minutes": 15, "mode": "train", "source": "demo"},
]
