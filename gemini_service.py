"""
gemini_service.py
Service layer for interacting with Google Gemini API using the official
Google GenAI Python SDK (`google-genai`).

Performs prompt construction, structured JSON generation, safe parsing,
strict SOH validation, and local status consistency reconciliation.
"""

import json
import re
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

import config
import battery_logic
import validators


SYSTEM_INSTRUCTION = """
You are an expert AI assistant specializing in lithium-ion EV battery health analysis and diagnostics.
Your task is to provide an AI-assisted State of Health (SOH) estimate based on seven cycle parameters.

CRITICAL GUIDELINES:
1. This is an AI-assisted estimate and NOT a laboratory measurement or certified battery-health diagnosis.
2. Do not invent unsupplied sensor measurements.
3. Do not claim absolute certainty.
4. Reason quantitatively using the supplied values and their physical electrochemical relationships:
   - Shorter discharge duration (tv_d) relative to charge duration indicates capacity fade.
   - Higher charging voltage (Eavg_ch) with lower discharging voltage (Eavg_d) indicates elevated internal resistance.
   - Elevated average cycle temperature (Tavg) and faster time to peak temperature (tTpeak_ch) correlate with thermal acceleration of degradation.
5. Strictly adhere to these project-defined demonstration thresholds:
   - SOH >= 90.0% -> HEALTHY
   - 85.0% <= SOH < 90.0% -> WARNING
   - SOH < 85.0% -> CRITICAL
6. Return only valid structured JSON.
"""


def _clean_json_text(text: str) -> str:
    """
    Strips markdown code fences (e.g. ```json ... ```) or surrounding whitespace.
    """
    cleaned = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    return cleaned


class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = (api_key or config.GEMINI_API_KEY).strip()
        self.model = (model or config.GEMINI_MODEL).strip()
        self.client: Optional[genai.Client] = None

        if self.is_configured:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self.client = None

    @property
    def is_configured(self) -> bool:
        """
        Returns True if a non-placeholder Gemini API key is configured.
        """
        placeholder_keys = {"", "YOUR_API_KEY_HERE", "YOUR_GEMINI_API_KEY", "NONE", "NULL"}
        return bool(self.api_key and self.api_key not in placeholder_keys and len(self.api_key) >= 10)

    def estimate_soh(self, params: Dict[str, float]) -> Dict[str, Any]:
        """
        Sends the 7 battery cycle parameters to Gemini API and returns validated SOH estimate.

        Expected output format:
        {
            "soh": 87.5,
            "status": "WARNING",
            "confidence": 0.72,
            "explanation": "...",
            "recommendation": "..."
        }
        """
        # 1. Validate inputs first
        is_valid, parsed_params, err_msg = validators.validate_battery_inputs(params)
        if not is_valid or parsed_params is None:
            raise ValueError(f"Input validation error: {err_msg}")

        # 2. Check API key configuration
        if not self.is_configured or self.client is None:
            raise ConnectionError(
                "Gemini API key is not configured. Please add your GEMINI_API_KEY to the .env file, "
                "or run in Demo Mode."
            )

        # 3. Construct user prompt with seven parameters
        prompt = (
            "You are assisting with lithium-ion EV battery health analysis.\n\n"
            "The application provides seven features derived from battery charge/discharge cycle data:\n"
            f"- tv_ch (charging voltage time): {parsed_params['tv_ch']} seconds\n"
            f"- tv_d (discharging voltage time): {parsed_params['tv_d']} seconds\n"
            f"- tI_ch (charging current time): {parsed_params['tI_ch']} seconds\n"
            f"- Tavg (average battery temperature): {parsed_params['Tavg']} °C\n"
            f"- tTpeak_ch (time to peak charging temperature): {parsed_params['tTpeak_ch']} seconds\n"
            f"- Eavg_ch (average charging voltage): {parsed_params['Eavg_ch']} V\n"
            f"- Eavg_d (average discharging voltage): {parsed_params['Eavg_d']} V\n\n"
            "Task:\n"
            "Provide an AI-assisted estimate of battery State of Health (SOH) as a percentage between 0 and 100.\n"
            "Remember: This is an AI-assisted estimate and not a laboratory measurement or certified battery-health diagnosis.\n"
            "Do not invent sensor measurements. Do not claim certainty.\n"
            "Use the supplied values and their relationships.\n\n"
            "Project-defined demonstration thresholds:\n"
            "- SOH >= 90.0% -> HEALTHY\n"
            "- 85.0% <= SOH < 90.0% -> WARNING\n"
            "- SOH < 85.0% -> CRITICAL\n\n"
            "Return ONLY valid structured JSON matching this exact structure:\n"
            "{\n"
            '    "soh": <float between 0.0 and 100.0>,\n'
            '    "status": "<HEALTHY | WARNING | CRITICAL>",\n'
            '    "confidence": <float between 0.0 and 1.0>,\n'
            '    "explanation": "<Concise, clear explanation understandable to a college-project audience>",\n'
            '    "recommendation": "<Appropriate monitoring or maintenance action>"\n'
            "}"
        )

        # 4. Call Gemini API using official Google GenAI Python SDK
        try:
            config_options = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config_options,
            )
        except APIError as api_err:
            raise RuntimeError(f"Gemini API Error: {api_err.message or str(api_err)}") from api_err
        except Exception as net_err:
            # Network failure, timeout, or DNS resolution issue
            err_str = str(net_err)
            if "API_KEY_INVALID" in err_str or "unregistered" in err_str.lower():
                raise ConnectionError("Invalid Gemini API key. Please check your key in the .env file.") from net_err
            raise RuntimeError(f"Network / Service communication error: {err_str}") from net_err

        # 5. Extract raw response text
        raw_text = response.text if response and hasattr(response, "text") else ""
        if not raw_text:
            raise ValueError("Gemini returned an empty response.")

        # 6. Parse JSON safely
        cleaned_json = _clean_json_text(raw_text)
        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError as json_err:
            raise ValueError(f"Failed to parse Gemini JSON output: {json_err}. Raw text: '{raw_text[:120]}...'") from json_err

        # 7. Validate output structure and ranges (0-100 SOH, 0-1 confidence)
        is_valid_resp, validated_data, val_err = validators.validate_gemini_response(parsed_data)
        if not is_valid_resp or validated_data is None:
            raise ValueError(f"Gemini output validation failed: {val_err}")

        # 8. Check status consistency against project-defined thresholds
        # If Gemini returned an inconsistent status, recalculate locally
        corrected_status = battery_logic.validate_status_consistency(
            validated_data["soh"], validated_data["status"]
        )
        validated_data["status"] = corrected_status
        validated_data["is_demo"] = False

        return validated_data
