# Architectural Specification: Farmer Crop & Weather Advisor

## 1. System Overview

The **Farmer Crop & Weather Advisor** is an event-driven, multi-agent cognitive architecture built on **LangGraph**. It combines structured weather telemetry via a custom **Model Context Protocol (MCP)** server, semantic agricultural knowledge retrieval via **ChromaDB RAG**, and dynamic web grounding via a **ReAct Alert Agent** using **Tavily**.

---

## 2. Agent Node Breakdown

```
[START]
   │
   ▼
[1. Supervisor Agent]
   │
   ├── (Missing Crop or Location?) ──► [END / Clarification Message]
   │
   ▼ (Valid Query + Resolved Coordinates)
[2. Forecast Agent] ◄───► [Custom MCP Server: 3 Tools]
   │
   ├── (Extreme Weather / Alert Detected?) ──► [3. Alert Agent (ReAct Loop, Max: 3)]
   │                                              │
   ▼ (Normal Weather)                             │
   └──────────────────────────────► [4. Crop Advisor Agent] ◄───► [ChromaDB RAG Guides]
                                       │
                                       ▼
                                    [5. Report Writer Agent]
                                       │
                                       ▼
                                     [END]
```

### 1. Supervisor Agent (`backend/agents/supervisor.py`)
- **Responsibility:** Intent classification, entity extraction (crop, location), and geocoding coordinates.
- **Guardrail:** If the farmer query lacks a specific crop or location, execution halts immediately and asks the user for clarification rather than hallucinating defaults.

### 2. Forecast Agent (`backend/agents/forecast_agent.py`)
- **Responsibility:** Queries the custom Weather MCP Server for:
  - 7-day daily forecast (temperature, precipitation, wind speed, weather code).
  - Past 7-day rainfall history.
  - Soil moisture profile (topsoil $0-3\text{ cm}$, root-zone $3-27\text{ cm}$).
- **Evaluation:** Analyzes thresholds (rain $>30\text{ mm}$, wind $>30\text{ km/h}$, thunderstorms) to set `extreme_weather_detected: bool`.

### 3. Alert Agent (`backend/agents/alert_agent.py`)
- **Pattern:** **ReAct Agent** (Reasoning + Action loop).
- **Tool:** Tavily Agricultural Web Search.
- **Safety Mechanism:** **Hard iteration limit `MAX_ITERATIONS = 3`** prevents infinite loops and uncontrolled API consumption.
- **Output:** Live IMD bulletins, cyclone track warnings, flood alerts, and current mandi market rates.

### 4. Crop Advisor Agent (`backend/agents/crop_advisor.py`)
- **Pattern:** Retrieval-Augmented Generation (RAG).
- **Knowledge Base:** ChromaDB loaded with official Tamil Nadu Agricultural University (TNAU) Agritech Guides for Paddy, Cotton, Banana, and Groundnut.
- **Guardrails Enforced:**
  - Prohibits foliar chemical spraying if wind $>15\text{ km/h}$ or rain is expected within $4-6\text{ hours}$.
  - Prohibits standing irrigation if soil moisture is saturated or heavy rain is forecast.
  - Never invents chemical dosages or off-label pesticides.

### 5. Report Writer Agent (`backend/agents/report_writer.py`)
- **Responsibility:** Synthesizes structured data from all agents into a simple, farmer-friendly advisory.
- **Citation Structure:** Formats explicit citations separating agricultural literature from live weather metrics and web links.
- **Uncertainty Notice:** Explicitly discloses meteorological forecast uncertainty.

---

## 3. Tool Specifications

### Custom Weather MCP Server (`backend/mcp_server/`)
1. `get_forecast(location, latitude, longitude)`
   - *Input:* Location name or latitude/longitude floats.
   - *Output:* JSON string containing 7-day daily forecast, WMO descriptions, precipitation sum, and summary warnings.
2. `get_rainfall_history(location, latitude, longitude, days)`
   - *Input:* Location name, coordinates, past days (1-30).
   - *Output:* JSON string with daily precipitation breakdown, past totals, and soil saturation index.
3. `get_soil_moisture(location, latitude, longitude)`
   - *Input:* Location name or coordinates.
   - *Output:* JSON string with topsoil and root-zone moisture ($m^3/m^3$), saturation percentage, and baseline irrigation advice.

### LangChain Tools (`backend/tools/`)
1. `GeocodingTool` (`resolve_location_coordinates`): Resolves arbitrary village/city names to GPS coordinates and administrative region names.
2. `TavilyAgriculturalSearchTool` (`tavily_agricultural_search`): Executes live web queries targeting disaster alerts, IMD updates, and mandi prices.

---

## 4. Shared State Specification (`backend/graph/state.py`)

```python
class FarmerAdvisorState(TypedDict):
    user_query: str
    crop: Optional[str]
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    missing_information: Optional[str]
    forecast: Optional[Dict[str, Any]]
    rainfall_history: Optional[Dict[str, Any]]
    soil_moisture: Optional[Dict[str, Any]]
    extreme_weather_detected: bool
    crop_guidance: Optional[Dict[str, Any]]
    rag_citations: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    market_information: Optional[Dict[str, Any]]
    web_sources: List[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    guardrail_warnings: List[str]
    final_report: Optional[str]
    sources: List[Dict[str, Any]]
    errors: Annotated[List[str], operator.add]
    iteration_count: int
    agent_logs: Annotated[List[str], operator.add]
```
