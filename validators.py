"""
validators.py
Validation functions for battery input parameters.
Ensures strict verification, boundary checking, and clean error messages
without raising unhandled exceptions or exposing stack traces to the user.
"""

import math
from typing import Dict, Tuple, Optional, Any, List
import config


REQUIRED_FIELDS = [p["id"] for p in config.PARAMETER_SPECS]
FIELD_NAMES = {p["id"]: p["label"] for p in config.PARAMETER_SPECS}
FIELD_SPECS = {p["id"]: p for p in config.PARAMETER_SPECS}


def validate_battery_inputs(
    raw_inputs: Dict[str, Any]
) -> Tuple[bool, Optional[List[float]], Optional[str]]:
    """
    Validates all 7 required battery parameters.
    
    Returns:
      (is_valid, parsed_values_list_or_None, error_message_or_None)
      
    Where parsed_values_list is ordered matching config.PARAMETER_SPECS.
    """
    # 1. Check for empty or missing inputs
    for field_id in REQUIRED_FIELDS:
        val = raw_inputs.get(field_id)
        if val is None or str(val).strip() == "":
            return False, None, "Please enter all seven battery parameters."

    # 2. Check for numeric validity
    parsed_values: List[float] = []
    for field_id in REQUIRED_FIELDS:
        val_str = str(raw_inputs[field_id]).strip()
        try:
            val_float = float(val_str)
        except (ValueError, TypeError):
            return False, None, "Please enter valid numerical values."

        if math.isnan(val_float) or math.isinf(val_float):
            return False, None, "Please enter valid numerical values."

        parsed_values.append(val_float)

    # 3. Check physical boundary plausibility
    for i, field_id in enumerate(REQUIRED_FIELDS):
        spec = FIELD_SPECS[field_id]
        val_float = parsed_values[i]
        label = spec["label"]
        min_val = spec.get("min_val")
        max_val = spec.get("max_val")
        unit = spec.get("unit_symbol", "")

        if min_val is not None and val_float < min_val:
            return (
                False,
                None,
                f"'{label}' cannot be less than {min_val} {unit}."
            )
        if max_val is not None and val_float > max_val:
            return (
                False,
                None,
                f"'{label}' exceeds realistic parameter bound of {max_val} {unit}."
            )

    return True, parsed_values, None
