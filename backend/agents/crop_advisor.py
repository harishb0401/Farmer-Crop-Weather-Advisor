"""Crop Advisor Agent: Retrieves RAG guidance, matches with weather, and enforces agronomic guardrails."""
import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from backend.graph.state import FarmerAdvisorState
from backend.rag.retriever import retrieve_agricultural_guidance
from backend.agents.llm import get_llm, extract_text_content
from backend.utils.timing import timed_operation

CROP_ADVISOR_PROMPT = """You are a Senior Agricultural Scientist & Crop Specialist.
Your role is to analyze a farmer's crop question by cross-referencing:
1. Grounded Agricultural RAG Guidance (with exact citations from TNAU Agritech).
2. Live 7-Day Forecast & Soil Moisture from MCP weather tools.
3. Historical rainfall totals.

STRICT AGRICULTURAL GUARDRAILS:
1. NEVER invent pesticide or chemical recommendations. Only recommend chemicals and dosages explicitly present in the provided RAG context.
2. DO NOT recommend chemical spraying if wind speed exceeds 15 km/h or if rain is forecasted within 4-6 hours.
3. If soil moisture is high (>0.35 m³/m³) or heavy rain (>20 mm) is coming, explicitly advise postponing or stopping irrigation.
4. If the provided RAG context does not contain sufficient reliable information for the specified crop, state clearly: "Reliable crop-specific guidance could not be found in the knowledge base."
5. Clearly cite the document title, source, and section for all agronomic claims.

Format your output in structured JSON:
{
  "irrigation_advice": "Specific irrigation recommendation with reasoning",
  "crop_protection_advice": "Pest/disease or field operation advice (or warning if weather unsuitable)",
  "what_to_avoid": "Specific practices to avoid (e.g. spraying in high wind, over-irrigating)",
  "agronomic_reasoning": "Scientific explanation linking weather conditions to plant physiology",
  "guardrail_applied": ["List of specific safety rules enforced"],
  "rag_citations_used": ["List of citation headers used"]
}
"""


@timed_operation("Crop Advisor Agent", start_emoji="⏳")
def crop_advisor_node(state: FarmerAdvisorState) -> Dict[str, Any]:
    """Retrieve RAG guidance and perform agronomic reasoning with strict guardrails."""
    crop = state.get("crop", "")
    location = state.get("location", "")
    query = state.get("user_query", "")
    forecast = state.get("forecast", {})
    soil = state.get("soil_moisture", {})
    rainfall_hist = state.get("rainfall_history", {})
    
    logs = [f"[Crop Advisor] Retrieving agricultural RAG guidance for crop: '{crop}'..."]
    errors = []
    guardrail_warnings = []

    # 1. Query RAG Knowledge Base
    rag_result = retrieve_agricultural_guidance(
        query=f"{crop} {query}",
        crop=crop,
        top_k=3
    )
    
    rag_citations = rag_result.get("citations", [])
    rag_text = rag_result.get("formatted_guidance", "")

    if rag_result.get("status") != "success" or not rag_citations:
        guardrail_warnings.append("Insufficient RAG knowledge: No verified agricultural document found for this specific crop.")
        rag_text = "No verified agricultural documents matched this crop."

    logs.append(f"[Crop Advisor] Retrieved {len(rag_citations)} RAG citations for {crop}.")

    # 2. Extract Weather Parameters for Guardrail Verification
    fc_days = forecast.get("forecast_days", [])
    max_wind = forecast.get("summary", {}).get("max_wind_kmh", 0)
    total_rain = forecast.get("summary", {}).get("total_expected_rainfall_mm", 0)
    soil_condition = soil.get("condition", "Unknown")
    
    # Pre-evaluate Weather Safety Guardrails
    if max_wind > 15:
        guardrail_warnings.append(f"High wind warning ({max_wind} km/h > 15 km/h limit): Foliar spraying prohibited to prevent drift.")
    if total_rain > 20:
        guardrail_warnings.append(f"Rainfall forecast ({total_rain} mm): Chemical spraying and heavy irrigation should be postponed.")
    if "Saturated" in soil_condition or "High" in soil_condition:
        guardrail_warnings.append(f"Soil status is {soil_condition}: Avoid additional irrigation; ensure field drainage.")

    # 3. LLM Agronomic Synthesis
    llm = get_llm(temperature=0.1)
    
    weather_summary_text = (
        f"Location: {location}\n"
        f"7-Day Total Rain: {total_rain} mm\n"
        f"Max Wind Speed: {max_wind} km/h\n"
        f"Soil Moisture: {soil.get('soil_metrics', {})} (Status: {soil_condition})\n"
        f"Past 7-Day Rainfall: {rainfall_hist.get('summary', {}).get('total_past_rainfall_mm', 0)} mm\n"
        f"Daily Forecast: {json.dumps(fc_days[:3])}"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=CROP_ADVISOR_PROMPT),
            HumanMessage(content=(
                f"Farmer Question: {query}\n"
                f"Target Crop: {crop}\n\n"
                f"=== RETRIEVED RAG AGRICULTURAL GUIDANCE ===\n{rag_text}\n\n"
                f"=== LIVE WEATHER & SOIL DATA ===\n{weather_summary_text}\n\n"
                f"=== PRE-COMPUTED GUARDRAILS ===\n{json.dumps(guardrail_warnings)}\n"
            ))
        ])
        
        raw_text = extract_text_content(response)
        # Parse JSON
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        recommendations = json.loads(raw_text)
    except Exception as e:
        errors.append(f"Crop advisor synthesis fallback: {str(e)}")
        recommendations = {
            "irrigation_advice": f"Adjust irrigation based on current soil condition ({soil_condition}) and expected rainfall ({total_rain} mm).",
            "crop_protection_advice": "Inspect crop for symptoms before chemical application. Follow label instructions.",
            "what_to_avoid": "Do not spray when wind exceeds 15 km/h or if rain is expected within 6 hours.",
            "agronomic_reasoning": "Standard agronomic guidelines apply.",
            "guardrail_applied": guardrail_warnings,
            "rag_citations_used": [c.get("document_title") for c in rag_citations]
        }

    logs.append(f"[Crop Advisor] Agronomic recommendations formulated with {len(guardrail_warnings)} guardrail rules.")

    return {
        "crop_guidance": recommendations,
        "rag_citations": rag_citations,
        "guardrail_warnings": guardrail_warnings,
        "agent_logs": logs,
        "errors": errors
    }
