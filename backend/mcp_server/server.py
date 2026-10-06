"""Custom Weather MCP Server for Agricultural Forecasting."""
import json
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

from backend.mcp_server.tools.forecast import get_forecast_tool
from backend.mcp_server.tools.rainfall import get_rainfall_history_tool
from backend.mcp_server.tools.soil_moisture import get_soil_moisture_tool

# Initialize FastMCP Server
mcp = FastMCP("FarmerWeatherServer")


@mcp.tool()
def get_forecast(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get a detailed 7-day weather forecast for agriculture.
    
    Includes daily min/max temperature, rainfall accumulation, rainfall probability,
    wind speed, and weather condition classification.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude (optional if location provided)
        longitude: Geographic longitude (optional if location provided)
    """
    result = get_forecast_tool(location=location, latitude=latitude, longitude=longitude)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_rainfall_history(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    days: int = 7
) -> str:
    """
    Get historical rainfall data for the previous N days (1 to 30 days).
    
    Includes daily rainfall totals, cumulative precipitation, and soil saturation assessment.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude
        longitude: Geographic longitude
        days: Number of past days to query (default: 7)
    """
    result = get_rainfall_history_tool(location=location, latitude=latitude, longitude=longitude, days=days)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_soil_moisture(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get estimated soil moisture profile across surface (0-3cm) and root-zone (3-27cm) layers.
    
    Provides moisture in m3/m3, saturation percentage, and baseline irrigation recommendation.
    
    Args:
        location: City/Town/Region name (e.g., 'Thanjavur')
        latitude: Geographic latitude
        longitude: Geographic longitude
    """
    result = get_soil_moisture_tool(location=location, latitude=latitude, longitude=longitude)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Run server via standard I/O transport
    mcp.run()
