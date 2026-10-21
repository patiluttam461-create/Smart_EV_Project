"""
demo_data.py
Demonstration battery cycle parameter profiles derived from the project's
processed dataset (final_anfis_dataset.csv).

These profiles represent verified operational cycle points corresponding to:
  - Healthy (SOH >= 90.0%)
  - Warning (85.0% <= SOH < 90.0%)
  - Critical (SOH < 85.0%)
"""

import os
from typing import Dict, Any, List
import pandas as pd
import config


# Pre-verified dataset points for immediate loading and fallback
VERIFIED_DATASET_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "healthy": {
        "title": "Healthy Example",
        "badge": "Healthy Condition (SOH ≥ 90.0%)",
        "description": "Early cycle stage (Cycle 1) with low internal resistance and high charge capacity.",
        "expected_soh": 97.45,
        "actual_soh": 97.50,
        "cycle": 1,
        "values": {
            "tv_ch": 5370.0,      # Charging voltage duration (seconds)
            "tv_d": 3600.0,       # Discharging voltage duration (seconds)
            "tI_ch": 7326.7,      # Charging current duration (seconds)
            "Tavg": 29.51,        # Average battery temperature (°C)
            "tTpeak_ch": 5161.0,  # Time to peak charging temperature (seconds)
            "Eavg_ch": 4.0865,    # Average charging voltage (V)
            "Eavg_d": 3.5813,     # Average discharging voltage (V)
        },
    },
    "warning": {
        "title": "Warning Example",
        "badge": "Warning Condition (85.0% ≤ SOH < 90.0%)",
        "description": "Mid-life cycle stage (Cycle 180) showing moderate degradation and capacity fade.",
        "expected_soh": 87.50,
        "actual_soh": 88.68,
        "cycle": 180,
        "values": {
            "tv_ch": 4640.4,      # Charging voltage duration (seconds)
            "tv_d": 3069.9,       # Discharging voltage duration (seconds)
            "tI_ch": 6687.9,      # Charging current duration (seconds)
            "Tavg": 22.38,        # Average battery temperature (°C)
            "tTpeak_ch": 4945.1,  # Time to peak charging temperature (seconds)
            "Eavg_ch": 4.1218,    # Average charging voltage (V)
            "Eavg_d": 3.5531,     # Average discharging voltage (V)
        },
    },
    "critical": {
        "title": "Critical Example",
        "badge": "Critical Condition (SOH < 85.0%)",
        "description": "Aged cycle stage (Cycle 305) with significant capacity degradation below 85%.",
        "expected_soh": 84.52,
        "actual_soh": 83.93,
        "cycle": 305,
        "values": {
            "tv_ch": 4391.5,      # Charging voltage duration (seconds)
            "tv_d": 2909.2,       # Discharging voltage duration (seconds)
            "tI_ch": 6315.2,      # Charging current duration (seconds)
            "Tavg": 24.04,        # Average battery temperature (°C)
            "tTpeak_ch": 4222.4,  # Time to peak charging temperature (seconds)
            "Eavg_ch": 4.1256,    # Average charging voltage (V)
            "Eavg_d": 3.5419,     # Average discharging voltage (V)
        },
    },
}


def get_demo_example(example_type: str) -> Dict[str, float]:
    """
    Retrieve parameter dictionary for a given demo example ('healthy', 'warning', 'critical').
    """
    key = example_type.strip().lower()
    if key not in VERIFIED_DATASET_EXAMPLES:
        raise KeyError(f"Unknown demo example type '{example_type}'. Choose from: healthy, warning, critical")
    return dict(VERIFIED_DATASET_EXAMPLES[key]["values"])


def get_demo_metadata(example_type: str) -> Dict[str, Any]:
    """
    Retrieve descriptive metadata for a demo example.
    """
    key = example_type.strip().lower()
    return VERIFIED_DATASET_EXAMPLES.get(key, {})
