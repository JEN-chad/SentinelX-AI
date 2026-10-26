"""SentinelX AI - Data Ingestion Validation Utilities

Validates numeric ranges, missing keys, and finite numeric values.
"""

import math
from typing import Any, Dict, List, Optional, Tuple


def is_valid_numeric(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Tuple[bool, Optional[float], Optional[str]]:
    """Validate and convert a numeric value, checking for NaN, Inf, and bounds."""
    if value is None:
        return False, None, "Value is None"

    try:
        val = float(value)
    except (ValueError, TypeError):
        return False, None, f"Cannot convert '{value}' to float"

    if math.isnan(val):
        return False, None, "Value is NaN"
    if math.isinf(val):
        return False, None, "Value is Infinite"

    if min_val is not None and val < min_val:
        return False, None, f"Value {val} is below minimum allowed {min_val}"
    if max_val is not None and val > max_val:
        return False, None, f"Value {val} exceeds maximum allowed {max_val}"

    return True, val, None


def validate_required_columns(row: Dict[str, Any], required_columns: List[str]) -> Tuple[bool, Optional[str]]:
    """Check that all required source columns are present."""
    # Strip whitespace in column keys for robust comparison
    clean_keys = {k.strip(): k for k in row.keys()}
    missing = [col for col in required_columns if col not in clean_keys]
    if missing:
        return False, f"Missing required columns: {missing}"
    return True, None
