"""Test suite for Weather MCP Server tools."""
import pytest
from backend.mcp_server.tools.forecast import get_forecast_tool, geocode_location
from backend.mcp_server.tools.rainfall import get_rainfall_history_tool
from backend.mcp_server.tools.soil_moisture import get_soil_moisture_tool


def test_geocoding_thanjavur():
    """Verify geocoding converts 'Thanjavur' to coordinates."""
    res = geocode_location("Thanjavur")
    assert res is not None, "Geocoding returned None"
    assert "latitude" in res
    assert "longitude" in res
    assert round(res["latitude"]) in (10, 11)
    print(f"\n[PASSED] Geocoded Thanjavur: Lat {res['latitude']}, Lon {res['longitude']}")


def test_get_forecast_thanjavur():
    """Verify 7-day forecast tool returns structured weather data."""
    res = get_forecast_tool(location="Thanjavur")
    assert res["status"] == "success"
    assert res["days_count"] >= 7
    assert len(res["forecast_days"]) >= 7
    first_day = res["forecast_days"][0]
    assert "temp_max_c" in first_day
    assert "rainfall_mm" in first_day
    assert "condition" in first_day
    print(f"\n[PASSED] Forecast: {res['days_count']} days retrieved. Summary: {res['summary']}")


def test_get_rainfall_history_thanjavur():
    """Verify historical rainfall tool returns past days data."""
    res = get_rainfall_history_tool(location="Thanjavur", days=7)
    assert res["status"] == "success"
    assert res["days_analyzed"] > 0
    assert "total_past_rainfall_mm" in res["summary"]
    print(f"\n[PASSED] Rainfall History: {res['days_analyzed']} days. Total: {res['summary']['total_past_rainfall_mm']} mm")


def test_get_soil_moisture_thanjavur():
    """Verify soil moisture tool returns layer metrics and saturation."""
    res = get_soil_moisture_tool(location="Thanjavur")
    assert res["status"] == "success"
    assert "soil_metrics" in res
    assert "saturation_percentage" in res["soil_metrics"]
    assert "irrigation_guidance" in res
    print(f"\n[PASSED] Soil Moisture: {res['condition']} - Guidance: {res['irrigation_guidance']}")


if __name__ == "__main__":
    print("Running MCP Tools Tests...")
    test_geocoding_thanjavur()
    test_get_forecast_thanjavur()
    test_get_rainfall_history_thanjavur()
    test_get_soil_moisture_thanjavur()
    print("\n All 3 MCP tools verified successfully!")
