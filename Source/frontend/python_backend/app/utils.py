"""Utility functions for API endpoints."""
from typing import Optional, List, Dict, Any
import json
import re


# UUID pattern for validation
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Severity display mapping
SEVERITY_DISPLAY_MAP = {
    'low': 'Low',
    'medium': 'Moderate', 
    'high': 'High',
    'critical': 'Severe',
    'operational': 'Operational',
}

# Role permissions mapping
ROLE_PERMISSIONS = {
    'Administrator': ['system_config', 'user_management', 'threshold_management', 'zone_management', 'risk_assessment', 'resource_deployment'],
    'Planner': ['risk_assessment', 'scenario_planning', 'alert_management', 'zone_viewing', 'reporting'],
    'Coordinator': ['resource_deployment', 'crew_management', 'communications', 'alert_management', 'zone_viewing'],
    'Data Analyst': ['data_export', 'reporting', 'analytics', 'zone_viewing'],
}


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    return bool(UUID_PATTERN.match(value))


def clamp(value: Any, min_val: float = 0, max_val: float = 1) -> float:
    """Clamp a value between min and max."""
    try:
        return min(max(float(value or 0), min_val), max_val)
    except (TypeError, ValueError):
        return 0.0


def determine_risk_band(value: float) -> str:
    """Determine risk band based on value."""
    if value >= 0.75:
        return 'Severe'
    if value >= 0.5:
        return 'High'
    if value >= 0.35:
        return 'Moderate'
    return 'Low'


def parse_point(geojson_text: Optional[str]) -> Dict[str, Optional[float]]:
    """Parse GeoJSON point to lat/lng dict."""
    if not geojson_text:
        return {'lat': None, 'lng': None}
    try:
        geometry = json.loads(geojson_text)
        if geometry and 'coordinates' in geometry:
            lng, lat = geometry['coordinates']
            return {'lat': lat, 'lng': lng}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    return {'lat': None, 'lng': None}


def format_risk_drivers(raw_factors: Any) -> List[Dict[str, Any]]:
    """Format risk factors into standardized driver format."""
    if not raw_factors:
        return []

    if isinstance(raw_factors, list):
        return [
            {
                'feature': entry.get('feature', 'factor'),
                'contribution': clamp(entry.get('contribution', 0)),
            }
            for entry in raw_factors
        ]

    if isinstance(raw_factors, dict):
        entries = list(raw_factors.items())
        total = sum(float(v or 0) for _, v in entries) or 1
        return [
            {
                'feature': feature,
                'contribution': round(float(value or 0) / total, 2),
            }
            for feature, value in entries
        ]

    return []


def get_alert_status(row: Dict[str, Any]) -> str:
    """Determine alert status from row data."""
    if row.get('resolved'):
        return 'resolved'
    if row.get('acknowledged'):
        return 'acknowledged'
    return 'open'


def get_alert_severity_display(value: str) -> str:
    """Get display name for severity."""
    return SEVERITY_DISPLAY_MAP.get(value, 'Moderate')


def determine_trend(current: Optional[float], previous: Optional[float], fallback: Optional[str] = None) -> str:
    """Determine trend direction based on values."""
    if current is None or previous is None:
        return fallback or 'steady'
    delta = float(current) - float(previous)
    if delta > 0.05:
        return 'rising'
    if delta < -0.05:
        return 'falling'
    return 'steady'


def normalize_timestamp(value: Optional[str]) -> Optional[str]:
    """Normalize timestamp format."""
    if not value:
        return None
    # Handle format like 2025-11-11T12-00-00Z
    if 'T' in value and '-' in value and ':' not in value:
        date_part, time_part_raw = value.split('T')
        has_zone = time_part_raw.endswith('Z')
        time_body = time_part_raw[:-1] if has_zone else time_part_raw
        normalized_time = time_body.replace('-', ':')
        return f"{date_part}T{normalized_time}{'Z' if has_zone else ''}"
    return value


def get_role_permissions(role: str) -> List[str]:
    """Get default permissions for a role."""
    return ROLE_PERMISSIONS.get(role, ['zone_viewing'])
