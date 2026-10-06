"""MCP Tool: Estimated Soil Moisture Profile via Open-Meteo."""
import requests
from typing import Dict, Any, Optional
from backend.mcp_server.tools.forecast import geocode_location
from backend.utils.timing import timed_operation


@timed_operation("MCP get_soil_moisture", start_emoji="💧")
def get_soil_moisture_tool(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Fetch estimated soil moisture across surface and root zone layers.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude
        longitude: Geographic longitude
        
    Returns:
        Structured soil moisture data including topsoil, root-zone saturation, and irrigation recommendations.
    """
    loc_meta = {}

    if (latitude is None or longitude is None) and location:
        geo = geocode_location(location)
        if not geo:
            return {
                "status": "error",
                "message": f"Could not geocode location: '{location}'"
            }
        latitude = geo["latitude"]
        longitude = geo["longitude"]
        loc_meta = geo
    elif latitude is None or longitude is None:
        return {
            "status": "error",
            "message": "Either 'location' or both 'latitude' and 'longitude' must be supplied."
        }

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": [
                "soil_moisture_0_to_1cm",
                "soil_moisture_1_to_3cm",
                "soil_moisture_3_to_9cm",
                "soil_moisture_9_to_27cm"
            ],
            "forecast_days": 1,
            "timezone": "auto"
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        hourly = data.get("hourly", {})
        sm_0_1 = hourly.get("soil_moisture_0_to_1cm", [])
        sm_1_3 = hourly.get("soil_moisture_1_to_3cm", [])
        sm_3_9 = hourly.get("soil_moisture_3_to_9cm", [])
        sm_9_27 = hourly.get("soil_moisture_9_to_27cm", [])

        # Take current or latest available reading (mean of first 12 hours)
        def safe_avg(lst):
            valid = [x for x in lst[:12] if x is not None]
            return sum(valid) / len(valid) if valid else 0.25

        surf_moisture = (safe_avg(sm_0_1) + safe_avg(sm_1_3)) / 2.0
        root_moisture = (safe_avg(sm_3_9) + safe_avg(sm_9_27)) / 2.0
        overall_avg = (surf_moisture + root_moisture) / 2.0

        # Typical soil moisture ranges in m³/m³:
        # < 0.15: Deficit / Dry
        # 0.15 - 0.35: Adequate / Optimal
        # 0.35 - 0.45: High / Wet
        # > 0.45: Saturated / Waterlogged
        if overall_avg < 0.15:
            condition = "Dry / Moisture Deficit"
            irrigation_status = "Irrigation Recommended (Soil moisture low)"
        elif 0.15 <= overall_avg <= 0.35:
            condition = "Optimal / Adequate Moisture"
            irrigation_status = "Optimal (Normal scheduled irrigation only)"
        elif 0.35 < overall_avg <= 0.45:
            condition = "High Moisture / Wet"
            irrigation_status = "Postpone Irrigation (High soil moisture)"
        else:
            condition = "Saturated / Waterlogged Risk"
            irrigation_status = "Do NOT Irrigate (Ensure drainage)"

        return {
            "status": "success",
            "location": loc_meta.get("name", location or f"{latitude},{longitude}"),
            "latitude": latitude,
            "longitude": longitude,
            "soil_metrics": {
                "topsoil_moisture_m3_m3": round(surf_moisture, 3),
                "root_zone_moisture_m3_m3": round(root_moisture, 3),
                "average_moisture_m3_m3": round(overall_avg, 3),
                "saturation_percentage": round(min(100.0, (overall_avg / 0.45) * 100), 1)
            },
            "condition": condition,
            "irrigation_guidance": irrigation_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve soil moisture: {str(e)}"
        }
