"""
battery_logic.py
Core ANFIS V5 inference engine and State of Health (SOH) evaluation pipeline.

Prediction Pipeline:
  Raw battery parameters (7 cycle features)
          ↓
  Feature scaling (MinMaxScaler)
          ↓
  ANFIS V5 Model (Gaussian MFs -> 128 Rules -> Normalization -> Sugeno Inference)
          ↓
  SOH Inverse Scaling (MinMaxScaler)
          ↓
  Predicted SOH %
          ↓
  Battery Condition Classification (Project-defined thresholds)

NOTE: The classification thresholds (HEALTHY >= 90%, WARNING 85-90%, CRITICAL < 85%)
are project-defined demonstration thresholds for educational/laboratory evaluation.
"""

import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import joblib
import config


# -------------------------------------------------------------
# Global Model State
# -------------------------------------------------------------
_is_loaded = False
_model_version = "ANFIS V5"
_centers: Optional[np.ndarray] = None
_sigmas: Optional[np.ndarray] = None
_consequents: Optional[np.ndarray] = None
_feature_scaler: Any = None
_soh_scaler: Any = None
_rules: Optional[np.ndarray] = None
_load_error: Optional[str] = None


def generate_rules(n_inputs: int = 7, n_mfs: int = 2) -> np.ndarray:
    """
    Generate all fuzzy-rule combinations.
    7 inputs with 2 MFs each -> 2^7 = 128 rules.
    """
    rules: List[List[int]] = []

    def recursive_build(current_rule: List[int], depth: int):
        if depth == n_inputs:
            rules.append(current_rule.copy())
            return
        for mf in range(n_mfs):
            current_rule.append(mf)
            recursive_build(current_rule, depth + 1)
            current_rule.pop()

    recursive_build([], 0)
    return np.array(rules, dtype=int)


def load_model() -> Tuple[bool, Optional[str]]:
    """
    Load ANFIS V5 model weights (.npz) and scalers (joblib .pkl).
    Checks local models/ folder first, then neighboring anfis models folder.
    """
    global _is_loaded, _centers, _sigmas, _consequents, _feature_scaler, _soh_scaler, _rules, _load_error

    if _is_loaded:
        return True, None

    model_path = config.MODEL_FILE
    feature_scaler_path = config.FEATURE_SCALER_FILE
    soh_scaler_path = config.SOH_SCALER_FILE

    # Check fallback directory if not found locally
    if not model_path.exists():
        fallback_model = config.ANFIS_FALLBACK_DIR / "anfis_v5_model.npz"
        if fallback_model.exists():
            model_path = fallback_model
            feature_scaler_path = config.ANFIS_FALLBACK_DIR / "feature_scaler.pkl"
            soh_scaler_path = config.ANFIS_FALLBACK_DIR / "soh_scaler.pkl"

    if not model_path.exists():
        _load_error = f"ANFIS model file not found at: {model_path}"
        return False, _load_error

    if not feature_scaler_path.exists():
        _load_error = f"Feature scaler file not found at: {feature_scaler_path}"
        return False, _load_error

    if not soh_scaler_path.exists():
        _load_error = f"SOH scaler file not found at: {soh_scaler_path}"
        return False, _load_error

    try:
        model_data = np.load(str(model_path))
        _centers = model_data["centers"]
        _sigmas = model_data["sigmas"]
        _consequents = model_data["consequents"]

        _feature_scaler = joblib.load(str(feature_scaler_path))
        _soh_scaler = joblib.load(str(soh_scaler_path))

        _rules = generate_rules(7, 2)
        _is_loaded = True
        _load_error = None
        return True, None
    except Exception as ex:
        _load_error = f"Failed to initialize ANFIS V5: {ex}"
        return False, _load_error


# Initialize model on module import
load_model()


def gaussian_membership(
    X: np.ndarray,
    centers: np.ndarray,
    sigmas: np.ndarray
) -> np.ndarray:
    """
    Calculate Gaussian membership values.
    X: shape (n_samples, 7)
    centers: shape (7, 2)
    sigmas: shape (7, 2)
    Returns: memberships shape (n_samples, 7, 2)
    """
    n_samples = X.shape[0]
    memberships = np.zeros((n_samples, 7, 2), dtype=float)

    for i in range(7):
        for m in range(2):
            c = centers[i, m]
            s = max(float(sigmas[i, m]), 0.05)
            memberships[:, i, m] = np.exp(-0.5 * ((X[:, i] - c) / s) ** 2)

    return memberships


def normalized_firing_strengths(
    X: np.ndarray,
    centers: np.ndarray,
    sigmas: np.ndarray
) -> np.ndarray:
    """
    Calculate normalized rule firing strengths for all 128 rules.
    """
    memberships = gaussian_membership(X, centers, sigmas)
    n_samples = X.shape[0]
    n_rules = _rules.shape[0] if _rules is not None else 128

    firing = np.ones((n_samples, n_rules), dtype=float)
    for r in range(n_rules):
        for i in range(7):
            mf_idx = _rules[r, i]  # type: ignore
            firing[:, r] *= memberships[:, i, mf_idx]

    denominator = np.sum(firing, axis=1, keepdims=True)
    denominator = np.maximum(denominator, 1e-12)
    return firing / denominator


def predict_soh_anfis(raw_values: List[float]) -> float:
    """
    Deterministic ANFIS prediction pipeline:
      1. Raw inputs (7 values) -> Feature scaling
      2. Normalized fuzzy rule firing strengths
      3. Zero-Order Sugeno consequence calculation
      4. SOH inverse transformation -> Actual SOH percentage
    """
    if not _is_loaded:
        ok, err = load_model()
        if not ok:
            raise RuntimeError(err or "ANFIS model is not loaded.")

    assert _centers is not None
    assert _sigmas is not None
    assert _consequents is not None
    assert _feature_scaler is not None
    assert _soh_scaler is not None

    X_raw = np.array([raw_values], dtype=float)

    # 1. Feature scaling
    X_scaled = _feature_scaler.transform(X_raw)

    # 2. Normalized firing strengths
    W_norm = normalized_firing_strengths(X_scaled, _centers, _sigmas)

    # 3. Sugeno linear inference
    pred_scaled = W_norm @ _consequents

    # 4. SOH inverse transformation
    pred_soh = _soh_scaler.inverse_transform(pred_scaled.reshape(-1, 1))

    return float(pred_soh[0, 0])


def get_status(soh: float) -> str:
    """
    Classify battery State of Health (SOH) based on project-defined thresholds:
      - SOH >= 90.0%: HEALTHY
      - 85.0% <= SOH < 90.0%: WARNING
      - SOH < 85.0%: CRITICAL
    """
    if soh >= 90.0:
        return "HEALTHY"
    elif soh >= 85.0:
        return "WARNING"
    else:
        return "CRITICAL"


def get_status_description(soh: float) -> str:
    """
    Return a clear academic description appropriate to the battery status,
    explicitly referencing project-defined classification thresholds.
    """
    status = get_status(soh)
    if status == "HEALTHY":
        return (
            f"State of Health is optimal at {soh:.2f}%. "
            "Battery operates within project-defined optimal capacity bounds (SOH ≥ 90.0%). "
            "Standard charging cycles and periodic impedance monitoring are recommended."
        )
    elif status == "WARNING":
        return (
            f"State of Health indicates moderate degradation at {soh:.2f}%. "
            "Capacity retention has dropped into the cautionary range (85.0% ≤ SOH < 90.0%). "
            "Increased internal resistance or thermal rise during charging may be present. "
            "Closer cycle monitoring and thermal management are recommended."
        )
    else:
        return (
            f"State of Health is critical at {soh:.2f}%. "
            "Capacity retention is below the project benchmark threshold (SOH < 85.0%). "
            "Significant degradation detected. Cell/pack diagnostic inspection or module replacement recommended."
        )


def get_status_color(status: str) -> str:
    """
    Return hex color code corresponding to battery status for dark dashboard styling.
    """
    status_upper = (status or "").upper()
    if status_upper == "HEALTHY":
        return config.COLOR_HEALTHY
    elif status_upper == "WARNING":
        return config.COLOR_WARNING
    elif status_upper == "CRITICAL":
        return config.COLOR_CRITICAL
    return config.COLOR_TEXT_MUTED


def check_training_range(raw_values: List[float]) -> List[str]:
    """
    Check if any of the 7 input values fall outside the ANFIS V5 training bounds.
    """
    if _feature_scaler is None:
        return []

    warnings: List[str] = []
    try:
        t_min = _feature_scaler.data_min_
        t_max = _feature_scaler.data_max_
        feature_names = [p["name"] for p in config.PARAMETER_SPECS]

        for i, name in enumerate(feature_names):
            val = raw_values[i]
            if val < t_min[i]:
                warnings.append(f"{name}: {val:.2f} < training min {t_min[i]:.2f}")
            elif val > t_max[i]:
                warnings.append(f"{name}: {val:.2f} > training max {t_max[i]:.2f}")
    except Exception:
        pass
    return warnings


def get_model_metadata() -> Dict[str, Any]:
    """
    Returns concise technical information about the ANFIS model architecture.
    """
    return {
        "model_name": "Adaptive Neuro-Fuzzy Inference System",
        "version": _model_version,
        "inference_type": "Zero-Order Sugeno ANFIS",
        "inputs": 7,
        "mfs_per_input": "2 Gaussian MFs / Input",
        "rules": 128,
        "output": "Battery SOH (%)",
        "model_type": "Regression",
        "features": "tv_ch, tv_d, tI_ch, Tavg, tTpeak_ch, Eavg_ch, Eavg_d",
        "is_loaded": _is_loaded,
        "status": "Ready for Prediction" if _is_loaded else "Error Loading Model",
        "error": _load_error,
    }
