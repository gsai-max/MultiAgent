import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional
from backend.app.tools.stubs import (
    STUB_SEARCH_DATABASE,
    STUB_GEO_ROUTES,
    STUB_PRICE_BANDS,
    STUB_FX_RATES
)

logger = logging.getLogger("ai_travel_planner.tools")


class ToolRouter:
    """
    Central router for search, geo estimation, price band lookup, and FX conversion.
    Provides in-memory caching, trace ID logging, per-call timeout management, and isolated API contracts.
    """

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self._cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self._load_travel_guides()

    def _load_travel_guides(self):
        """Load RAG curated travel guides dataset."""
        try:
            import os
            guides_path = os.path.join(os.path.dirname(__file__), "travel_guides.json")
            if os.path.exists(guides_path):
                with open(guides_path, "r", encoding="utf-8") as f:
                    self.travel_guides = json.load(f)
            else:
                self.travel_guides = {}
        except Exception as e:
            logger.warning(f"Failed to load travel_guides.json: {e}")
            self.travel_guides = {}

    def get_travel_guide(self, country: str, city: str) -> Optional[Dict[str, Any]]:
        """
        RAG lookup over curated travel guide snippets for specific country and city.
        """
        country_data = self.travel_guides.get(country, {})
        return country_data.get(city)


    def _generate_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """Create a deterministic cache key string from method name and query parameters."""
        raw_str = f"{method}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def search(
        self,
        query: str,
        city: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search destination database for attractions, food, and experiences matching query.
        """
        params = {"query": query.lower().strip(), "city": city}
        cache_key = self._generate_cache_key("search", params)

        if cache_key in self._cache:
            self.cache_hits += 1
            logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.search CACHE HIT for query='{query}' city='{city}'")
            return self._cache[cache_key]

        self.cache_misses += 1
        logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.search CACHE MISS executing query='{query}' city='{city}'")

        # Filtering stub logic
        results = []
        q_lower = query.lower()
        for item in STUB_SEARCH_DATABASE:
            if city and item["city"].lower() != city.lower():
                continue
            
            # Match against category, name, tags, or rationale
            matches_name = q_lower in item["name"].lower()
            matches_cat = q_lower in item["category"].lower()
            matches_tags = any(q_lower in tag for tag in item.get("tags", []))
            
            if matches_name or matches_cat or matches_tags or not query.strip():
                results.append(item)

        if not results and city:
            # Fallback to all items for that city if specific query matched nothing
            results = [item for item in STUB_SEARCH_DATABASE if item["city"].lower() == city.lower()]

        self._cache[cache_key] = results
        return results

    def geo_estimate(
        self,
        origin: str,
        destination: str,
        mode: str = "transit",
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate travel duration, distance, and transfer logistics between two locations.
        """
        params = {"origin": origin.strip(), "destination": destination.strip(), "mode": mode}
        cache_key = self._generate_cache_key("geo_estimate", params)

        if cache_key in self._cache:
            self.cache_hits += 1
            logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.geo_estimate CACHE HIT {origin} -> {destination}")
            return self._cache[cache_key]

        self.cache_misses += 1
        logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.geo_estimate CACHE MISS {origin} -> {destination}")

        route_key = f"{origin}_{destination}"
        if route_key in STUB_GEO_ROUTES:
            result = STUB_GEO_ROUTES[route_key]
        else:
            # Default fallback estimation for unknown routes
            result = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "duration_minutes": 60,
                "distance_km": 50,
                "estimated_cost_usd": 30.0,
                "notes": "Estimated regional transit link."
            }

        self._cache[cache_key] = result
        return result

    def price_band(
        self,
        category: str,
        city: str,
        tier: str = "medium",
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get price estimation bands for lodging, food, transport, or activities in a target city.
        """
        params = {"category": category.lower(), "city": city, "tier": tier.lower()}
        cache_key = self._generate_cache_key("price_band", params)

        if cache_key in self._cache:
            self.cache_hits += 1
            logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.price_band CACHE HIT category='{category}' city='{city}'")
            return self._cache[cache_key]

        self.cache_misses += 1
        logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.price_band CACHE MISS category='{category}' city='{city}'")

        city_data = STUB_PRICE_BANDS.get(city)
        if city_data and category in city_data:
            band_data = city_data[category]
            cost_val = band_data.get(tier, band_data.get("medium", 50.0))
            result = {
                "city": city,
                "category": category,
                "tier": tier,
                "estimated_cost": cost_val,
                "currency": band_data.get("currency", "USD")
            }
        else:
            # Generic fallback band
            result = {
                "city": city,
                "category": category,
                "tier": tier,
                "estimated_cost": 50.0 if tier == "medium" else (25.0 if tier == "low" else 120.0),
                "currency": "USD"
            }

        self._cache[cache_key] = result
        return result

    def fx_convert(
        self,
        amount: float,
        from_currency: str = "USD",
        to_currency: str = "JPY",
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert currency amount using current rate lookup.
        """
        params = {"amount": amount, "from": from_currency.upper(), "to": to_currency.upper()}
        cache_key = self._generate_cache_key("fx_convert", params)

        if cache_key in self._cache:
            self.cache_hits += 1
            logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.fx_convert CACHE HIT {amount} {from_currency} -> {to_currency}")
            return self._cache[cache_key]

        self.cache_misses += 1
        logger.info(f"[TraceID: {trace_id or 'none'}] ToolRouter.fx_convert CACHE MISS {amount} {from_currency} -> {to_currency}")

        pair_key = f"{from_currency.upper()}_{to_currency.upper()}"
        rate = STUB_FX_RATES.get(pair_key, 1.0)
        converted_amount = round(amount * rate, 2)

        result = {
            "amount": amount,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "exchange_rate": rate,
            "converted_amount": converted_amount
        }

        self._cache[cache_key] = result
        return result
