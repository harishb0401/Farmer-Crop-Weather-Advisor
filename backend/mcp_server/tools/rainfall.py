"""MCP Tool: Historical Rainfall Data via Open-Meteo."""
import requests
from typing import Dict, Any, Optional
from backend.mcp_server.tools.forecast import geocode_location
from backend.utils.timing import timed_operation


@timed_operation("MCP get_rainfall_history", start_emoji="🌧️")
def get_rainfall_history_tool(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    Fetch historical rainfall totals and daily breakdown for the past N days.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude
        longitude: Geographic longitude
        days: Number of previous days to query (default 7, max 30)
        
    Returns:
        Structured historical rainfall records, daily totals, and cumulative summary.
    """
    days = min(max(1, days), 30) # clamp between 1 and 30 days
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
            "past_days": days,
            "forecast_days": 1,
            "daily": ["precipitation_sum", "rain_sum"],
            "timezone": "auto"
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        daily = data.get("daily", {})
        times = daily.get("time", [])
        precip = daily.get("precipitation_sum", [])

        # The last element is today's forecast; earlier elements are the requested past days
        past_records = []
        # Exclude the forecast portion if present
        history_len = min(days, len(times) - 1 if len(times) > 1 else len(times))
        
        for i in range(history_len):
            past_records.append({
                "date": times[i],
                "rainfall_mm": precip[i] if precip[i] is not None else 0.0
            })

        total_rainfall = sum(r["rainfall_mm"] for r in past_records)
        rainy_days = sum(1 for r in past_records if r["rainfall_mm"] > 2.5)

        return {
            "status": "success",
            "location": loc_meta.get("name", location or f"{latitude},{longitude}"),
            "latitude": latitude,
            "longitude": longitude,
            "days_analyzed": len(past_records),
            "daily_records": past_records,
            "summary": {
                "total_past_rainfall_mm": round(total_rainfall, 2),
                "rainy_days_count": rainy_days,
                "average_daily_rainfall_mm": round(total_rainfall / max(1, len(past_records)), 2),
                "soil_saturation_risk": "High" if total_rainfall > 60 else "Moderate" if total_rainfall > 25 else "Low"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve rainfall history: {str(e)}"
        }
