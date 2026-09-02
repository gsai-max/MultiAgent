import logging
from typing import Optional, Any
from backend.app.schemas.domain import TravelConstraints
from backend.app.services.llm_client import LLMClient

logger = logging.getLogger("ai_travel_planner.orchestrator.extract")

SYSTEM_PROMPT_CONSTRAINT_EXTRACTION = """
You are the Constraint Extractor component of the AI Travel Planner Orchestrator.
Your sole job is to convert a natural language travel request into a strictly structured TravelConstraints object.

Instructions:
1. Extract the destination region or country (e.g. "Japan", "Italy", "California").
2. Extract all explicitly mentioned or implied target cities (e.g. ["Tokyo", "Kyoto"]). If only a country is specified, infer 1-2 major destination cities.
3. Extract total trip duration in days as an integer (e.g. 5).
4. Extract total overall budget cap as a number. If currency symbol like "$" or "€" or "¥" is present, extract budget_total and set currency accordingly (e.g., USD, EUR, JPY). Default currency to "USD" if unspecified.
5. Extract key preferences (interests, food, sightseeing, culture).
6. Extract avoidances (e.g. crowds, rush hour, expensive taxis, long bus rides).
7. Extract hard requirements (non-negotiable constraints explicitly requested by user).
8. Extract soft preferences (optional preferences).
"""


class ConstraintExtractor:
    """Orchestrator Part A: Natural language request -> TravelConstraints."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def extract(
        self,
        user_request: str,
        mock_response: Optional[Any] = None
    ) -> TravelConstraints:
        """Extract TravelConstraints from user request string."""
        logger.info(f"Extracting TravelConstraints for request: '{user_request[:60]}...'")

        if self.llm_client.is_mock and mock_response is None:
            # Provide intelligent mock extraction based on request content for dry runs
            mock_response = self._fallback_mock_extraction(user_request)

        constraints = self.llm_client.extract_structured(
            prompt=user_request,
            response_model=TravelConstraints,
            system_prompt=SYSTEM_PROMPT_CONSTRAINT_EXTRACTION,
            temperature=0.1,
            mock_response=mock_response
        )
        logger.info(f"Extracted constraints: {constraints.destination_region}, {constraints.cities}, {constraints.duration_days}d, ${constraints.budget_total}")
        return constraints

    def _fallback_mock_extraction(self, user_request: str) -> TravelConstraints:
        """Helper mock extractor for dry-runs without LLM API key."""
        req_lower = user_request.lower()
        cities = []
        if "tokyo" in req_lower:
            cities.append("Tokyo")
        if "kyoto" in req_lower:
            cities.append("Kyoto")
        if "osaka" in req_lower:
            cities.append("Osaka")
        if not cities:
            cities = ["Tokyo", "Kyoto"]

        duration = 5
        for word in req_lower.split():
            if word.isdigit():
                duration = int(word)
                break

        return TravelConstraints(
            destination_region="Japan",
            cities=cities,
            duration_days=duration,
            budget_total=3000.0,
            currency="USD",
            preferences=["temples", "food", "sightseeing"],
            avoidances=["crowds"],
            hard_requirements=[],
            soft_preferences=[]
        )
