"""MCP Tool: 7-Day Weather Forecast via Open-Meteo."""
import requests
from typing import Dict, Any, Optional
from backend.utils.timing import timed_operation

def geocode_location(location_name: str) -> Optional[Dict[str, Any]]:
    """Geocode a location name to lat/long using Open-Meteo Geocoding API."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location_name)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("results"):
            top = data["results"][0]
            return {
                "name": top.get("name"),
                "latitude": top.get("latitude"),
                "longitude": top.get("longitude"),
                "country": top.get("country"),
                "admin1": top.get("admin1", "")
            }
    except Exception as e:
        return None
    return None


@timed_operation("MCP get_forecast", start_emoji="🌤️")
def get_forecast_tool(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Fetch a detailed 7-day agricultural weather forecast.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude
        longitude: Geographic longitude
        
    Returns:
        Structured 7-day forecast including temperature, rainfall, humidity, wind, and conditions.
    """
    loc_meta = {}
    if (latitude is None or longitude is None) and location:
        geo = geocode_location(location)
        if not geo:
            return {
                "status": "error",
                "message": f"Could not geocode location: '{location}'. Please verify the spelling or provide coordinates."
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
        # Request daily parameters relevant to agriculture
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max"
            ],
            "hourly": [
                "relative_humidity_2m"
            ],
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        precip_prob = daily.get("precipitation_probability_max", [])
        wind = daily.get("wind_speed_10m_max", [])
        w_codes = daily.get("weather_code", [])

        # WMO Weather interpretation mapping
        def interpret_wmo(code: int) -> str:
            if code == 0: return "Clear Sky"
            elif code in (1, 2, 3): return "Mainly Clear / Partly Cloudy"
            elif code in (45, 48): return "Foggy"
            elif code in (51, 53, 55): return "Drizzle"
            elif code in (61, 63, 65): return "Rain (Light to Heavy)"
            elif code in (71, 73, 75): return "Snow"
            elif code in (80, 81, 82): return "Rain Showers"
            elif code in (95, 96, 99): return "Thunderstorm / Severe Weather"
            return "Overcast"

        forecast_days = []
        total_precip = sum([p for p in precip if p is not None])
        max_wind = max([w for w in wind if w is not None]) if wind else 0.0

        for i in range(len(dates)):
            forecast_days.append({
                "date": dates[i],
                "condition": interpret_wmo(w_codes[i] if i < len(w_codes) else 0),
                "temp_max_c": t_max[i] if i < len(t_max) else None,
                "temp_min_c": t_min[i] if i < len(t_min) else None,
                "rainfall_mm": precip[i] if i < len(precip) else 0.0,
                "rainfall_prob_pct": precip_prob[i] if i < len(precip_prob) else 0,
                "wind_speed_kmh": wind[i] if i < len(wind) else 0.0
            })

        # Calculate high level alerts summary
        extreme_weather = False
        warnings = []
        if total_precip > 50.0:
            extreme_weather = True
            warnings.append(f"Heavy cumulative rainfall expected: {total_precip:.1f} mm over 7 days.")
        if max_wind > 40.0:
            extreme_weather = True
            warnings.append(f"High wind gusts expected up to {max_wind:.1f} km/h.")
        if any(c in (95, 96, 99) for c in w_codes):
            extreme_weather = True
            warnings.append("Thunderstorms forecasted.")

        return {
            "status": "success",
            "location": loc_meta.get("name", location or f"{latitude},{longitude}"),
            "latitude": latitude,
            "longitude": longitude,
            "days_count": len(forecast_days),
            "forecast_days": forecast_days,
            "summary": {
                "total_expected_rainfall_mm": round(total_precip, 2),
                "max_wind_kmh": max_wind,
                "extreme_weather_indicated": extreme_weather,
                "warnings": warnings
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve forecast from Open-Meteo: {str(e)}"
        }
