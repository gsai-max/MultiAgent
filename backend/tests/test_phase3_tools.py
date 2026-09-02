"""Phase 3 Test Suite: Tool Router capabilities & caching."""

import pytest
from backend.app.tools.router import ToolRouter


@pytest.fixture
def router():
    return ToolRouter()


def test_tool_router_search(router):
    results = router.search(query="temple", city="Kyoto", trace_id="trace-test-01")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("Fushimi Inari" in item["name"] for item in results)
    assert all(item["city"] == "Kyoto" for item in results)


def test_tool_router_search_food(router):
    results = router.search(query="ramen", city="Tokyo", trace_id="trace-test-02")
    assert len(results) >= 1
    assert "Yanaka Ginza" in results[0]["name"]


def test_tool_router_geo_estimate(router):
    route = router.geo_estimate(origin="Tokyo", destination="Kyoto", mode="Shinkansen", trace_id="trace-test-03")
    assert route["origin"] == "Tokyo"
    assert route["destination"] == "Kyoto"
    assert route["mode"] == "Shinkansen"
    assert route["duration_minutes"] == 135
    assert route["estimated_cost_usd"] == 130.0


def test_tool_router_price_band(router):
    tokyo_lodging = router.price_band(category="lodging", city="Tokyo", tier="medium", trace_id="trace-test-04")
    assert tokyo_lodging["estimated_cost"] == 140.0

    kyoto_food = router.price_band(category="food", city="Kyoto", tier="medium", trace_id="trace-test-05")
    assert kyoto_food["estimated_cost"] == 50.0


def test_tool_router_fx_convert(router):
    conversion = router.fx_convert(amount=100.0, from_currency="USD", to_currency="JPY", trace_id="trace-test-06")
    assert conversion["amount"] == 100.0
    assert conversion["from_currency"] == "USD"
    assert conversion["to_currency"] == "JPY"
    assert conversion["exchange_rate"] == 150.0
    assert conversion["converted_amount"] == 15000.0


def test_tool_router_in_memory_caching(router):
    # Initial call -> cache miss
    res1 = router.search(query="temple", city="Kyoto")
    assert router.cache_misses == 1
    assert router.cache_hits == 0

    # Second call with identical params -> cache hit
    res2 = router.search(query="temple", city="Kyoto")
    assert router.cache_misses == 1
    assert router.cache_hits == 1
    assert res1 == res2


def test_tool_router_trace_propagation(caplog, router):
    with caplog.at_level("INFO"):
        router.search(query="ramen", city="Tokyo", trace_id="trace-unique-abc-999")
        assert "trace-unique-abc-999" in caplog.text
