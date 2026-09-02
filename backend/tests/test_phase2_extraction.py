"""Phase 2 Test Suite: LLM Client & Constraint Extraction."""

import pytest
from pydantic import ValidationError
from backend.app.schemas.domain import TravelConstraints
from backend.app.services.llm_client import LLMClient, clean_json_string
from backend.app.services.constraint_extractor import ConstraintExtractor


def test_clean_json_string():
    raw_markdown = "```json\n{\n  \"key\": \"value\"\n}\n```"
    cleaned = clean_json_string(raw_markdown)
    assert cleaned == "{\n  \"key\": \"value\"\n}"


def test_llm_client_mock_extraction():
    client = LLMClient(api_key="mock")
    mock_payload = {
        "destination_region": "Japan",
        "cities": ["Tokyo", "Kyoto"],
        "duration_days": 5,
        "budget_total": 3000.0,
        "currency": "USD",
        "preferences": ["food", "temples"],
        "avoidances": ["crowds"],
        "hard_requirements": [],
        "soft_preferences": []
    }
    extracted = client.extract_structured(
        prompt="5 day trip to Tokyo and Kyoto",
        response_model=TravelConstraints,
        mock_response=mock_payload
    )
    assert extracted.destination_region == "Japan"
    assert extracted.duration_days == 5
    assert "Tokyo" in extracted.cities


class MockClientWithRepair(LLMClient):
    """Subclass LLMClient to simulate 1st attempt failure and 2nd attempt success."""
    def __init__(self):
        super().__init__(api_key="fake-key-for-test")
        self.call_count = 0

    def _call_raw_llm(self, prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
        self.call_count += 1
        if self.call_count == 1:
            # 1st attempt: return invalid payload (missing duration_days)
            return '{"destination_region": "Japan", "cities": ["Tokyo"], "budget_total": 3000.0}'
        else:
            # 2nd attempt (repair retry): return valid payload
            return (
                '{"destination_region": "Japan", "cities": ["Tokyo", "Kyoto"], '
                '"duration_days": 5, "budget_total": 3000.0, "currency": "USD", '
                '"preferences": ["food"], "avoidances": ["crowds"], '
                '"hard_requirements": [], "soft_preferences": []}'
            )


def test_llm_client_repair_loop_success():
    mock_llm = MockClientWithRepair()
    extracted = mock_llm.extract_structured(
        prompt="5 day trip to Tokyo",
        response_model=TravelConstraints
    )
    assert mock_llm.call_count == 2
    assert extracted.duration_days == 5
    assert extracted.destination_region == "Japan"


class MockClientFailsTwice(LLMClient):
    """Subclass LLMClient to simulate failures on both attempts."""
    def __init__(self):
        super().__init__(api_key="fake-key-for-test")

    def _call_raw_llm(self, prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
        return '{"invalid_json": true}'


def test_llm_client_repair_loop_failure():
    mock_llm = MockClientFailsTwice()
    with pytest.raises(ValueError, match="Failed to extract valid TravelConstraints"):
        mock_llm.extract_structured(
            prompt="5 day trip to Tokyo",
            response_model=TravelConstraints
        )


def test_constraint_extractor_sample_request():
    extractor = ConstraintExtractor()
    sample_request = "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples, avoid crowds"
    
    constraints = extractor.extract(sample_request)
    
    assert isinstance(constraints, TravelConstraints)
    assert constraints.destination_region == "Japan"
    assert "Tokyo" in constraints.cities
    assert "Kyoto" in constraints.cities
    assert constraints.duration_days == 5
    assert constraints.budget_total == 3000.0
    assert "food" in constraints.preferences or "temples" in constraints.preferences
    assert "crowds" in constraints.avoidances
