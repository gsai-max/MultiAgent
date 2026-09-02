import json
import logging
import re
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel, ValidationError
from backend.app.config import settings

logger = logging.getLogger("ai_travel_planner.llm")

T = TypeVar("T", bound=BaseModel)


def clean_json_string(raw_text: str) -> str:
    """Extract clean JSON substring from raw model output text."""
    cleaned = raw_text.strip()
    # Strip markdown block fences ```json ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


class LLMClient:
    """LLM client handling low-temperature structured output generation prioritizing Groq API free models."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY or settings.LLM_API_KEY
        self.model_name = model_name or settings.LLM_MODEL
        self.is_mock = not self.api_key or self.api_key.lower() in ("mock", "your_api_key_here", "")

    def _call_raw_llm(self, prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
        """Execute raw LLM API call prioritizing Groq API (free open models), with OpenAI / Google GenAI fallbacks."""
        if self.is_mock:
            raise RuntimeError("API Key not configured. Use mock mode or set GROQ_API_KEY / LLM_API_KEY.")

        # 1. Attempt call via Groq SDK
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            return completion.choices[0].message.content
        except Exception as groq_err:
            logger.info(f"groq SDK call not available or failed: {groq_err}. Attempting Groq OpenAI-compatible client...")

        # 2. Attempt call via OpenAI client pointing to Groq API endpoint
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            return completion.choices[0].message.content
        except Exception as groq_openai_err:
            logger.warning(f"Groq API endpoint call failed: {groq_openai_err}. Attempting standard OpenAI / GenAI fallbacks...")

        # 3. Fallback to standard OpenAI client
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            return completion.choices[0].message.content
        except Exception as openai_err:
            # 4. Fallback to google-genai
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config={"temperature": temperature}
                )
                return response.text
            except Exception as genai_err:
                logger.error(f"All LLM calls failed: {genai_err}")
                raise RuntimeError(f"LLM API execution failed: {genai_err}") from genai_err


    def extract_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str = "",
        temperature: float = 0.1,
        mock_response: Optional[Any] = None
    ) -> T:
        """
        Extract structured Pydantic object from LLM response with low temperature and 1-retry repair logic.
        """
        # Handle mock response override (useful for unit tests or dry runs)
        if mock_response is not None:
            if isinstance(mock_response, response_model):
                return mock_response
            if isinstance(mock_response, dict):
                return response_model.model_validate(mock_response)
            if isinstance(mock_response, str):
                cleaned = clean_json_string(mock_response)
                return response_model.model_validate_json(cleaned)

        if self.is_mock:
            logger.info("Operating in Mock Mode for LLM extraction.")

        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        augmented_system_prompt = (
            f"{system_prompt}\n\n"
            f"CRITICAL REQUIREMENT: Return ONLY a valid JSON object matching the JSON Schema below.\n"
            f"Do not include commentary, markdown wrapper codeblocks, or explanatory prose.\n\n"
            f"JSON Schema:\n{schema_json}"
        ).strip()

        # Attempt 1
        logger.info(f"Executing LLM extraction attempt 1 for model {response_model.__name__}")
        raw_output = ""
        last_error = ""
        try:
            raw_output = self._call_raw_llm(prompt, system_prompt=augmented_system_prompt, temperature=temperature)
            cleaned_output = clean_json_string(raw_output)
            return response_model.model_validate_json(cleaned_output)
        except (ValidationError, json.JSONDecodeError, Exception) as err:
            last_error = str(err)
            logger.warning(f"LLM extraction attempt 1 failed with error: {last_error}. Triggering single-retry repair loop.")

        # Attempt 2 (Single Repair Retry Loop)
        repair_prompt = (
            f"Original user request:\n{prompt}\n\n"
            f"Your previous JSON output attempt was:\n{raw_output}\n\n"
            f"Validation Error:\n{last_error}\n\n"
            f"Please correct the output so that it strictly satisfies the required JSON Schema."
        )

        try:
            repaired_raw = self._call_raw_llm(repair_prompt, system_prompt=augmented_system_prompt, temperature=temperature)
            cleaned_repaired = clean_json_string(repaired_raw)
            return response_model.model_validate_json(cleaned_repaired)
        except (ValidationError, json.JSONDecodeError, Exception) as err2:
            logger.error(f"LLM extraction repair attempt 2 also failed: {err2}")
            raise ValueError(f"Failed to extract valid {response_model.__name__} after repair retry. Error: {err2}") from err2
