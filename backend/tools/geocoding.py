"""LangChain Tool: Geocoding and Location Resolution."""
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests


class GeocodingInput(BaseModel):
    location_name: str = Field(
        description="Name of the village, city, district, or region in India or globally (e.g. 'Thanjavur', 'Madurai', 'Guntur')."
    )


class GeocodingTool(BaseTool):
    name: str = "resolve_location_coordinates"
    description: str = (
        "Converts a location name into latitude, longitude, and administrative region details. "
        "Useful before querying weather models or local agricultural advisories."
    )
    args_schema: Type[BaseModel] = GeocodingInput

    def _run(self, location_name: str) -> Dict[str, Any]:
        """Execute geocoding lookup."""
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location_name)}&count=1&language=en&format=json"
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data.get("results"):
                top = data["results"][0]
                return {
                    "status": "success",
                    "found": True,
                    "name": top.get("name"),
                    "latitude": top.get("latitude"),
                    "longitude": top.get("longitude"),
                    "country": top.get("country"),
                    "admin_state": top.get("admin1", ""),
                    "display_name": f"{top.get('name')}, {top.get('admin1', '')}, {top.get('country', '')}"
                }
            return {
                "status": "not_found",
                "found": False,
                "message": f"Location '{location_name}' could not be resolved."
            }
        except Exception as e:
            return {
                "status": "error",
                "found": False,
                "message": f"Geocoding service error: {str(e)}"
            }
