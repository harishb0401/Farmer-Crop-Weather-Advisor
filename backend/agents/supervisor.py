"""Supervisor Agent: Intent classification, entity extraction, and input guardrails."""
import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from backend.graph.state import FarmerAdvisorState
from backend.agents.llm import get_llm, extract_text_content
from backend.tools.geocoding import GeocodingTool
from backend.utils.timing import timed_operation

SUPERVISOR_PROMPT = """You are the Lead Agricultural Supervisor Agent in a multi-agent system.
Your job is to analyze the farmer's query and extract the following essential parameters in strict JSON format:
1. "crop": The specific crop mentioned (e.g. "paddy", "cotton", "banana", "groundnut", "wheat", "rice", etc.). If no crop is mentioned, return null.
2. "location": The specific village, town, district, or region mentioned (e.g. "Thanjavur", "Madurai", "Guntur", "Salem"). If no location is mentioned, return null.
3. "intent": One of ["irrigation_advice", "pesticide_spraying", "disaster_protection", "harvest_timing", "general_advisory"].
4. "urgency": One of ["normal", "high", "critical"] (e.g. cyclone/flood mentions indicate critical).

Respond ONLY with valid JSON with no markdown backticks or commentary.
Example:
{"crop": "paddy", "location": "Thanjavur", "intent": "irrigation_advice", "urgency": "normal"}
"""


@timed_operation("Supervisor Agent", start_emoji="⏳")
def supervisor_node(state: FarmerAdvisorState) -> Dict[str, Any]:
    """Analyze query and extract entities with strict missing information guardrails."""
    query = state.get("user_query", "")
    llm = get_llm(temperature=0.0)
    geocoder = GeocodingTool()

    log_entry = f"[Supervisor] Analyzing user query: '{query}'"
    errors = []
    
    extracted = {"crop": None, "location": None, "intent": "general_advisory", "urgency": "normal"}
    
    try:
        response = llm.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=f"Farmer query: {query}")
        ])
        raw_text = extract_text_content(response)
        # Clean json formatting if wrapped
        raw_text = re.sub(r"^```json\s*|```$", "", raw_text, flags=re.MULTILINE).strip()
        extracted = json.loads(raw_text)
    except Exception as e:
        errors.append(f"Supervisor extraction fallback: {str(e)}")

    # Heuristic fallback if LLM missed either parameter
    q_lower = query.lower()
    if not extracted.get("crop"):
        for crop_name in ["paddy", "rice", "cotton", "banana", "groundnut", "wheat", "maize", "sugarcane", "plantain"]:
            if crop_name in q_lower:
                extracted["crop"] = "banana" if crop_name == "plantain" else ("paddy" if crop_name == "rice" else crop_name)
                break

    if not extracted.get("location"):
        # Match 'near <place>', 'in <place>', 'at <place>'
        loc_match = re.search(r"\b(?:near|in|at|around|for)\s+([A-Z][a-z]+|[a-z]+)", query, re.IGNORECASE)
        if loc_match:
            candidate = loc_match.group(1).strip()
            # Avoid matching common words
            if candidate.lower() not in ["the", "my", "our", "this", "next", "these", "a", "an", "banana", "paddy", "cotton", "groundnut"]:
                extracted["location"] = candidate.capitalize()
        if not extracted.get("location"):
            for loc_name in ["thanjavur", "tanjore", "cuddalore", "madurai", "coimbatore", "chennai", "trichy", "salem", "guntur", "vellore", "erode"]:
                if loc_name in q_lower:
                    extracted["location"] = loc_name.capitalize()
                    break

    crop = extracted.get("crop")
    location = extracted.get("location")

    # Guardrail Check 1 & 2: Missing Location or Missing Crop
    missing_items = []
    if not crop:
        missing_items.append("the crop you are growing (e.g., Paddy, Cotton, Banana, Groundnut)")
    if not location:
        missing_items.append("your farm location or district (e.g., Thanjavur, Madurai, Guntur)")

    if missing_items:
        clarification_msg = (
            "🌾 **Farmer Advisory System Notice**\n\n"
            "To give you accurate, localized agricultural and weather advice, please tell me:\n"
            + "\n".join(f"- **{item}**" for item in missing_items)
            + "\n\n*Example:* 'I grow paddy near Thanjavur. Should I irrigate this week?'"
        )
        return {
            "crop": crop,
            "location": location,
            "missing_information": clarification_msg,
            "final_report": clarification_msg,
            "agent_logs": [log_entry, f"[Supervisor Guardrail] Missing required inputs: {missing_items}"],
            "errors": errors
        }

    # Resolve coordinates via Geocoding Tool
    lat, lon = None, None
    geo_res = geocoder.invoke({"location_name": location})
    if geo_res.get("found"):
        lat = geo_res.get("latitude")
        lon = geo_res.get("longitude")
        location = geo_res.get("display_name", location)

    return {
        "crop": crop.lower(),
        "location": location,
        "latitude": lat,
        "longitude": lon,
        "missing_information": None,
        "agent_logs": [log_entry, f"[Supervisor] Extracted crop='{crop}', location='{location}' ({lat}, {lon})"],
        "errors": errors
    }
