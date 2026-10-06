"""Forecast Agent Node: Calls Weather MCP tools and evaluates meteorological risks."""
from typing import Dict, Any
from backend.graph.state import FarmerAdvisorState
from backend.mcp_server.tools.forecast import get_forecast_tool
from backend.mcp_server.tools.rainfall import get_rainfall_history_tool
from backend.mcp_server.tools.soil_moisture import get_soil_moisture_tool
from backend.utils.timing import timed_operation


@timed_operation("Forecast Agent", start_emoji="⏳")
def forecast_node(state: FarmerAdvisorState) -> Dict[str, Any]:
    """Execute Weather MCP tools and evaluate severe weather conditions."""
    location = state.get("location")
    lat = state.get("latitude")
    lon = state.get("longitude")
    user_query = state.get("user_query", "").lower()
    
    logs = [f"[Forecast Agent] Querying Weather MCP tools for '{location}' ({lat}, {lon})..."]
    errors = []
    sources = []

    # 1. MCP Tool 1: 7-Day Forecast
    forecast_data = get_forecast_tool(location=location, latitude=lat, longitude=lon)
    if forecast_data.get("status") != "success":
        errors.append(f"Forecast tool warning: {forecast_data.get('message')}")
    else:
        sources.append({
            "type": "MCP Weather Tool",
            "name": "Open-Meteo 7-Day Forecast API",
            "details": f"Coordinates ({lat}, {lon})"
        })

    # 2. MCP Tool 2: Rainfall History
    rainfall_data = get_rainfall_history_tool(location=location, latitude=lat, longitude=lon, days=7)
    if rainfall_data.get("status") != "success":
        errors.append(f"Rainfall history tool warning: {rainfall_data.get('message')}")
    else:
        sources.append({
            "type": "MCP Weather Tool",
            "name": "Open-Meteo Historical Precipitation API",
            "details": f"Past 7 days analysis for {location}"
        })

    # 3. MCP Tool 3: Soil Moisture Estimation
    soil_data = get_soil_moisture_tool(location=location, latitude=lat, longitude=lon)
    if soil_data.get("status") != "success":
        errors.append(f"Soil moisture tool warning: {soil_data.get('message')}")
    else:
        sources.append({
            "type": "MCP Weather Tool",
            "name": "Open-Meteo Soil Profile Model (0-27cm)",
            "details": f"Estimated volumetric moisture for {location}"
        })

    # Detect Extreme Weather or Disasters
    extreme_weather = False
    warning_reasons = []

    # Check forecast summary
    if forecast_data.get("status") == "success":
        fc_summary = forecast_data.get("summary", {})
        if fc_summary.get("extreme_weather_indicated"):
            extreme_weather = True
            warning_reasons.extend(fc_summary.get("warnings", []))
        if fc_summary.get("total_expected_rainfall_mm", 0) > 30.0:
            extreme_weather = True
            warning_reasons.append(f"High cumulative rainfall expected ({fc_summary.get('total_expected_rainfall_mm')} mm)")
        if fc_summary.get("max_wind_kmh", 0) > 30.0:
            extreme_weather = True
            warning_reasons.append(f"High wind speeds ({fc_summary.get('max_wind_kmh')} km/h)")

    # Check query explicit keywords
    alert_keywords = ["cyclone", "flood", "storm", "heatwave", "heavy rain", "alert", "warning", "gale", "hurricane"]
    if any(kw in user_query for kw in alert_keywords):
        extreme_weather = True
        warning_reasons.append("User query explicitly requests disaster/severe alert assessment.")

    logs.append(f"[Forecast Agent] Weather evaluation complete. Extreme Weather = {extreme_weather}. Reasons: {warning_reasons}")

    return {
        "forecast": forecast_data,
        "rainfall_history": rainfall_data,
        "soil_moisture": soil_data,
        "extreme_weather_detected": extreme_weather,
        "sources": sources,
        "agent_logs": logs,
        "errors": errors
    }
