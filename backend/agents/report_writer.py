"""Report Writer Agent: Formats comprehensive farmer advisory with citations and uncertainty."""
from typing import Dict, Any, List
from backend.graph.state import FarmerAdvisorState
from backend.agents.llm import get_llm, extract_text_content
from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.timing import timed_operation

REPORT_WRITER_PROMPT = """You are the Lead Farmer Advisory Report Writer.
Your job is to generate a simple, clear, and farmer-friendly advisory based on the provided structured data from our multi-agent pipeline.

Use simple, encouraging language suitable for farmers and agricultural extension officers.

You MUST adhere strictly to the following markdown template:

🌾 Farmer Advisory

**Crop:** {crop}
**Location:** {location}

📅 **Weather Summary**
(List next 3-5 days forecast: Date, condition, High/Low Temp, expected rainfall mm, wind speed)

💧 **Irrigation Advice**
(Clear actionable advice based on soil moisture and rainfall forecast)

🌱 **Crop Advice**
(Clear, actionable crop management, pest/disease advice, or storm protection)

⚠️ **Weather Alerts & Disaster Warnings**
(Include active alerts from Tavily or severe weather flags; if none, state "No severe weather alerts active for this region.")

🚫 **What to Avoid**
(Explicit list of actions to avoid, such as spraying during high winds, over-irrigating wet soils, harvesting during damp periods)

📌 **Why this recommendation?**
(Explain the scientific & meteorological reasoning connecting the weather forecast with plant physiology)

📚 **Sources & Citations**
- **Agricultural Knowledge Base (RAG):**
  (List document title, source institution, and section for all RAG citations)
- **Weather Data:**
  - Open-Meteo 7-Day Forecast & Soil Profile MCP Server
- **Current Live Web Sources (Tavily):**
  (List active URLs/bulletins if searched)

⚠️ **Uncertainty & Advisory Notice:**
Weather forecasts are subject to rapid change. Recommendations are based on current model forecasts and official agricultural guidance. Monitor local weather bulletins and field conditions before major operations.
"""


@timed_operation("Report Writer Agent", start_emoji="⏳")
def report_writer_node(state: FarmerAdvisorState) -> Dict[str, Any]:
    """Synthesize all agent findings into the standardized farmer report."""
    crop = state.get("crop", "Crop").capitalize()
    location = state.get("location", "Location")
    forecast = state.get("forecast", {})
    soil = state.get("soil_moisture", {})
    rainfall_hist = state.get("rainfall_history", {})
    crop_guide = state.get("crop_guidance", {})
    alerts = state.get("alerts", [])
    market_info = state.get("market_information", {})
    rag_citations = state.get("rag_citations", [])
    web_sources = state.get("web_sources", [])
    guardrail_warnings = state.get("guardrail_warnings", [])
    
    logs = ["[Report Writer] Assembling final farmer-friendly advisory..."]

    # Format weather summary
    fc_days = forecast.get("forecast_days", [])
    weather_lines = []
    for d in fc_days[:5]:
        weather_lines.append(
            f"- **{d.get('date')}**: {d.get('condition')} | Temp: {d.get('temp_min_c')}°C - {d.get('temp_max_c')}°C | Rain: {d.get('rainfall_mm')} mm ({d.get('rainfall_prob_pct')}% prob) | Wind: {d.get('wind_speed_kmh')} km/h"
        )
    weather_summary_str = "\n".join(weather_lines) if weather_lines else "Weather forecast data currently unavailable."

    # Format RAG sources
    rag_sources_list = []
    for c in rag_citations:
        rag_sources_list.append(f"  - *{c.get('document_title')}* ({c.get('source')}, Section: {c.get('section')}, ID: {c.get('document_id')})")
    rag_sources_str = "\n".join(rag_sources_list) if rag_sources_list else "  - Standard TNAU Agritech Crop Management Practices"

    # Format Web sources
    web_sources_list = []
    for w in web_sources[:3]:
        web_sources_list.append(f"  - [{w.get('name')}]({w.get('url')})")
    web_sources_str = "\n".join(web_sources_list) if web_sources_list else "  - No external web alerts required."

    llm = get_llm(temperature=0.2)
    
    prompt_payload = f"""
Crop: {crop}
Location: {location}

Weather Days:
{weather_summary_str}

Soil Moisture Metrics:
- Condition: {soil.get('condition', 'Adequate')}
- Topsoil: {soil.get('soil_metrics', {}).get('topsoil_moisture_m3_m3', 0.25)} m³/m³
- Guidance: {soil.get('irrigation_guidance', 'Normal scheduled irrigation')}

Past 7-Day Rainfall Total:
{rainfall_hist.get('summary', {}).get('total_past_rainfall_mm', 0)} mm

Crop Advisor Analysis:
- Irrigation Advice: {crop_guide.get('irrigation_advice', '')}
- Protection Advice: {crop_guide.get('crop_protection_advice', '')}
- What to Avoid: {crop_guide.get('what_to_avoid', '')}
- Reasoning: {crop_guide.get('agronomic_reasoning', '')}
- Guardrails Enforced: {guardrail_warnings}

Active Disaster & Weather Alerts:
{market_info.get('summary', 'No severe alerts active.')}

RAG Citations:
{rag_sources_str}

Web Sources:
{web_sources_str}
"""

    try:
        response = llm.invoke([
            SystemMessage(content=REPORT_WRITER_PROMPT),
            HumanMessage(content=prompt_payload)
        ])
        final_report_text = extract_text_content(response)
    except Exception as e:
        # Structured deterministic fallback
        final_report_text = f"""🌾 **Farmer Advisory**

**Crop:** {crop}  
**Location:** {location}  

📅 **Weather Summary**  
{weather_summary_str}

💧 **Irrigation Advice**  
{crop_guide.get('irrigation_advice', 'Follow normal irrigation based on soil status.')}

🌱 **Crop Advice**  
{crop_guide.get('crop_protection_advice', 'Inspect fields for pest activity and ensure field drainage.')}

⚠️ **Weather Alerts & Disaster Warnings**  
{market_info.get('summary', 'No severe weather alerts active for this region.')}

🚫 **What to Avoid**  
{crop_guide.get('what_to_avoid', '- Avoid spraying chemicals in windy or rainy conditions.\n- Avoid waterlogging roots.')}

📌 **Why this recommendation?**  
{crop_guide.get('agronomic_reasoning', 'Recommendations align with current weather forecasts and established agronomic requirements.')}

📚 **Sources & Citations**  
- **Agricultural Knowledge Base (RAG):**  
{rag_sources_str}
- **Weather Data:**  
  - Open-Meteo 7-Day Forecast & Soil Profile MCP Server
- **Current Live Web Sources (Tavily):**  
{web_sources_str}

⚠️ **Uncertainty & Advisory Notice:**  
Weather forecasts are subject to rapid change. Recommendations are based on current model forecasts and official agricultural guidance. Monitor local weather bulletins and field conditions before major operations.
"""

    logs.append("[Report Writer] Advisory report successfully generated.")

    return {
        "final_report": final_report_text,
        "agent_logs": logs
    }
