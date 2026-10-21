"""
config.py
Configuration settings for Smart EV Battery Management System.
Defines project branding, parameter specifications, model paths,
and design constants for the ANFIS engineering dashboard.
"""

from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Application Identity & Branding
APP_TITLE = "SMART EV BATTERY MANAGEMENT SYSTEM"
APP_SUBTITLE = "ANFIS-Based Battery State of Health Estimation"
APP_BADGE = "ANFIS MODEL ACTIVE"
APP_FOOTER = "Soft Computing + AIML Project • ANFIS-Based EV Battery State of Health Estimation"

# Battery SOH Thresholds (Project-defined demonstration thresholds)
SOH_HEALTHY_MIN = 90.0
SOH_WARNING_MIN = 85.0

# 7 Battery Parameters Specification
# Order must strictly match the trained ANFIS model feature order
PARAMETER_SPECS = [
    {
        "id": "tv_ch",
        "name": "tv_ch",
        "label": "Charging Voltage Time (tv_ch)",
        "unit": "seconds",
        "unit_symbol": "s",
        "meaning": "Charging voltage duration in seconds",
        "hint": "e.g. 5370.0",
        "min_val": 0.0,
        "max_val": 50000.0,
    },
    {
        "id": "tv_d",
        "name": "tv_d",
        "label": "Discharging Voltage Time (tv_d)",
        "unit": "seconds",
        "unit_symbol": "s",
        "meaning": "Discharging voltage duration in seconds",
        "hint": "e.g. 3600.0",
        "min_val": 0.0,
        "max_val": 50000.0,
    },
    {
        "id": "tI_ch",
        "name": "tI_ch",
        "label": "Charging Current Time (tI_ch)",
        "unit": "seconds",
        "unit_symbol": "s",
        "meaning": "Charging current duration in seconds",
        "hint": "e.g. 7326.7",
        "min_val": 0.0,
        "max_val": 50000.0,
    },
    {
        "id": "Tavg",
        "name": "Tavg",
        "label": "Average Battery Temperature (Tavg)",
        "unit": "°C",
        "unit_symbol": "°C",
        "meaning": "Average battery temperature across cycle in °C",
        "hint": "e.g. 29.5",
        "min_val": -40.0,
        "max_val": 120.0,
    },
    {
        "id": "tTpeak_ch",
        "name": "tTpeak_ch",
        "label": "Time to Peak Temperature (tTpeak_ch)",
        "unit": "seconds",
        "unit_symbol": "s",
        "meaning": "Time to peak charging temperature in seconds",
        "hint": "e.g. 5161.0",
        "min_val": 0.0,
        "max_val": 50000.0,
    },
    {
        "id": "Eavg_ch",
        "name": "Eavg_ch",
        "label": "Average Charging Voltage (Eavg_ch)",
        "unit": "V",
        "unit_symbol": "V",
        "meaning": "Average cell voltage during charge in Volts",
        "hint": "e.g. 4.09",
        "min_val": 0.1,
        "max_val": 10.0,
    },
    {
        "id": "Eavg_d",
        "name": "Eavg_d",
        "label": "Average Discharging Voltage (Eavg_d)",
        "unit": "V",
        "unit_symbol": "V",
        "meaning": "Average cell voltage during discharge in Volts",
        "hint": "e.g. 3.58",
        "min_val": 0.1,
        "max_val": 10.0,
    },
]

# Model and Scaler File Paths
MODELS_DIR = BASE_DIR / "models"
MODEL_FILE = MODELS_DIR / "anfis_v5_model.npz"
FEATURE_SCALER_FILE = MODELS_DIR / "feature_scaler.pkl"
SOH_SCALER_FILE = MODELS_DIR / "soh_scaler.pkl"
DATASET_FILE = BASE_DIR / "data" / "processed" / "final_anfis_dataset.csv"

# Fallback path if models are in neighboring directory
ANFIS_FALLBACK_DIR = BASE_DIR.parent / "smart_ev_battery_anfis" / "models"

# Visual Theme Colors (Dark Engineering Dashboard)
COLOR_BG = "#0B1220"          # Deep Navy Background
COLOR_CARD = "#111827"        # Dark Card Background
COLOR_CARD_BORDER = "#1E293B" # Card Outline Border
COLOR_INPUT_BG = "#1E293B"    # Input Field Background
COLOR_INPUT_BORDER = "#334155"# Input Field Border
COLOR_INPUT_FOCUS = "#38BDF8" # Input Field Focused Border
COLOR_ACCENT_BLUE = "#0284C7" # Electric Blue Primary Accent
COLOR_ACCENT_CYAN = "#38BDF8" # Cyan Focus / Highlight Accent
COLOR_TEXT_PRIMARY = "#F8FAFC"# High Contrast White Text
COLOR_TEXT_MUTED = "#94A3B8"  # Slate Muted Text
COLOR_TEXT_DIM = "#64748B"    # Dim Caption Text

# Status Colors
COLOR_HEALTHY = "#10B981"     # Emerald Green
COLOR_WARNING = "#F59E0B"     # Amber Orange
COLOR_CRITICAL = "#EF4444"    # Crimson Red
