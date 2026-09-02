"""Static stub datasets for ToolRouter."""

from typing import List, Dict, Any

STUB_SEARCH_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "act_tokyo_01",
        "city": "Tokyo",
        "name": "Senso-ji Temple & Asakusa Stroll",
        "category": "temple",
        "estimated_duration_hours": 2.5,
        "crowd_level": "medium",
        "cost_band": "$",
        "estimated_cost": 15.0,
        "must_do": True,
        "rationale": "Historic temple in Asakusa with vibrant traditional shopping street.",
        "tags": ["temple", "culture", "historic"]
    },
    {
        "id": "act_tokyo_02",
        "city": "Tokyo",
        "name": "Yanaka Ginza Neighborhood Walk & Local Ramen",
        "category": "food",
        "estimated_duration_hours": 3.0,
        "crowd_level": "low",
        "cost_band": "$$",
        "estimated_cost": 35.0,
        "must_do": False,
        "rationale": "Authentic ramen and low-crowd retro neighborhood walk.",
        "tags": ["food", "ramen", "neighborhood", "low_crowd"]
    },
    {
        "id": "act_tokyo_03",
        "city": "Tokyo",
        "name": "Tsukiji Outer Market Food Exploration",
        "category": "food",
        "estimated_duration_hours": 2.0,
        "crowd_level": "medium",
        "cost_band": "$$",
        "estimated_cost": 40.0,
        "must_do": True,
        "rationale": "Fresh seafood street food tasting in morning hours.",
        "tags": ["food", "seafood", "market"]
    },
    {
        "id": "act_kyoto_01",
        "city": "Kyoto",
        "name": "Fushimi Inari Shrine Early Morning Visit",
        "category": "temple",
        "estimated_duration_hours": 3.0,
        "crowd_level": "low",
        "cost_band": "$",
        "estimated_cost": 0.0,
        "must_do": True,
        "rationale": "Iconic thousands of vermilion torii gates visited early to avoid crowds.",
        "tags": ["temple", "shrine", "iconic", "low_crowd"]
    },
    {
        "id": "act_kyoto_02",
        "city": "Kyoto",
        "name": "Arashiyama Bamboo Grove & Tenryu-ji",
        "category": "nature",
        "estimated_duration_hours": 3.5,
        "crowd_level": "medium",
        "cost_band": "$$",
        "estimated_cost": 25.0,
        "must_do": False,
        "rationale": "Scenic bamboo paths and tranquil Zen temple garden.",
        "tags": ["nature", "bamboo", "temple", "garden"]
    },
    {
        "id": "act_kyoto_03",
        "city": "Kyoto",
        "name": "Gion Evening Historic District Stroll",
        "category": "culture",
        "estimated_duration_hours": 2.0,
        "crowd_level": "medium",
        "cost_band": "$",
        "estimated_cost": 0.0,
        "must_do": False,
        "rationale": "Preserved traditional wooden machiya architecture and teahouses.",
        "tags": ["culture", "gion", "neighborhood", "evening"]
    }
]

STUB_GEO_ROUTES: Dict[str, Dict[str, Any]] = {
    "Tokyo_Kyoto": {
        "origin": "Tokyo",
        "destination": "Kyoto",
        "mode": "Shinkansen",
        "duration_minutes": 135,
        "distance_km": 460,
        "estimated_cost_usd": 130.0,
        "notes": "Tokaido Shinkansen Nozomi train."
    },
    "Kyoto_Tokyo": {
        "origin": "Kyoto",
        "destination": "Tokyo",
        "mode": "Shinkansen",
        "duration_minutes": 135,
        "distance_km": 460,
        "estimated_cost_usd": 130.0,
        "notes": "Tokaido Shinkansen Nozomi train return."
    },
    "Tokyo_Osaka": {
        "origin": "Tokyo",
        "destination": "Osaka",
        "mode": "Shinkansen",
        "duration_minutes": 150,
        "distance_km": 500,
        "estimated_cost_usd": 140.0,
        "notes": "Tokaido Shinkansen Nozomi train."
    },
    "Kyoto_Osaka": {
        "origin": "Kyoto",
        "destination": "Osaka",
        "mode": "Rapid Train",
        "duration_minutes": 30,
        "distance_km": 45,
        "estimated_cost_usd": 6.0,
        "notes": "JR Special Rapid Service train."
    }
}

STUB_PRICE_BANDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Tokyo": {
        "lodging": {"low": 80.0, "medium": 140.0, "high": 300.0, "currency": "USD"},
        "food": {"low": 30.0, "medium": 60.0, "high": 150.0, "currency": "USD"},
        "transport": {"low": 10.0, "medium": 20.0, "high": 50.0, "currency": "USD"},
        "activities": {"low": 10.0, "medium": 30.0, "high": 80.0, "currency": "USD"}
    },
    "Kyoto": {
        "lodging": {"low": 90.0, "medium": 180.0, "high": 350.0, "currency": "USD"},
        "food": {"low": 25.0, "medium": 50.0, "high": 120.0, "currency": "USD"},
        "transport": {"low": 8.0, "medium": 15.0, "high": 40.0, "currency": "USD"},
        "activities": {"low": 5.0, "medium": 25.0, "high": 70.0, "currency": "USD"}
    }
}

STUB_FX_RATES: Dict[str, float] = {
    "USD_JPY": 150.0,
    "JPY_USD": 0.00667,
    "EUR_USD": 1.08,
    "USD_EUR": 0.925,
    "GBP_USD": 1.28,
    "USD_USD": 1.0
}
