# 🌾 Farmer Crop & Weather Advisor

An autonomous multi-agent AI system designed for farmers, agricultural extension officers, and Farmer Producer Organisations (FPOs). The system combines live meteorological forecasts, historical rainfall data, estimated soil moisture profiles, agricultural RAG knowledge, real-time disaster alerts via Tavily web search, and mandi market prices.

---

## 🏗️ System Architecture & Workflow

```mermaid
flowchart TD
    User([🌾 Farmer Query]) --> Sup[1. Supervisor Agent]
    
    subgraph Input Guardrails
        Sup -->|Missing Crop / Location| AskUser([💬 Clarification Notice])
    end

    Sup -->|Valid Query & Coordinates| FC[2. Forecast Agent]
    
    subgraph Custom Weather MCP Server
        FC -->|get_forecast| M1[(Open-Meteo 7-Day Forecast)]
        FC -->|get_rainfall_history| M2[(Open-Meteo Rainfall History)]
        FC -->|get_soil_moisture| M3[(Open-Meteo Soil Profile 0-27cm)]
    end

    FC --> Cond{⚠️ Extreme Weather Detected?}
    
    subgraph ReAct Alert Loop
        Cond -->|YES / High Risk| Alert[3. Alert Agent (ReAct Loop)]
        Alert <-->|Tavily API| Web[(Live IMD Bulletins & Mandi Rates)]
    end
    
    Cond -->|NO| Crop[4. Crop Advisor Agent]
    Alert --> Crop
    
    subgraph Agricultural RAG Knowledge Base
        Crop <-->|Vector Retrieval| Chroma[(ChromaDB: TNAU Agritech Guides)]
    end

    Crop --> Rep[5. Report Writer Agent]
    Rep --> Guard[Agronomic Guardrails & Verification]
    Guard --> Final([📋 Farmer Advisory Report])
```

---

## ✅ Mandatory Course Requirements Checklist

| Requirement | Implementation Detail | Status |
| :--- | :--- | :---: |
| **1. Custom MCP server (≥3 tools)** | FastMCP server running in `backend/mcp_server/server.py` | ✅ |
| **2. MCP Tool: get_forecast** | 7-day agricultural forecast in `backend/mcp_server/tools/forecast.py` | ✅ |
| **3. MCP Tool: get_rainfall_history** | Past precipitation analysis in `backend/mcp_server/tools/rainfall.py` | ✅ |
| **4. MCP Tool: get_soil_moisture** | Multi-layer soil profile ($0-27\text{ cm}$) in `backend/mcp_server/tools/soil_moisture.py` | ✅ |
| **5. ≥2 LangChain tools** | Geocoding Tool & Tavily Agricultural Search Tool | ✅ |
| **6. RAG Pipeline with citations** | ChromaDB with TNAU Agritech documents (Paddy, Cotton, Banana, Groundnut) | ✅ |
| **7. Tavily web search** | Real-time disaster alerts, cyclone warnings, and mandi market prices | ✅ |
| **8. ReAct agent with hard limit** | `Alert Agent` ReAct loop with `MAX_ITERATIONS = 3` | ✅ |
| **9. LangGraph orchestration** | StateGraph coordinating 5 distinct agents in `backend/graph/workflow.py` | ✅ |
| **10. Shared state between agents** | `FarmerAdvisorState` TypedDict in `backend/graph/state.py` | ✅ |
| **11. Conditional routing** | Dynamic branch: Extreme Weather ➔ ReAct Alert Agent vs Direct Crop Advisor | ✅ |
| **12. Guardrails & Citations** | Input validation, chemical dosage constraints, wind/rain thresholds, uncertainty statement | ✅ |

---

## 📁 Project Structure

```text
farmer-crop-weather-advisor/
├── backend/
│   ├── agents/
│   │   ├── supervisor.py         # Entity extraction & missing input guardrails
│   │   ├── forecast_agent.py     # Weather MCP consumer & risk evaluator
│   │   ├── alert_agent.py        # ReAct agent with hard iteration limit (Tavily)
│   │   ├── crop_advisor.py       # RAG retriever & agronomic reasoning
│   │   ├── report_writer.py      # Final synthesis with citations & uncertainty
│   │   └── llm.py                # Multi-model resilient LLM factory
│   │
│   ├── graph/
│   │   ├── state.py              # FarmerAdvisorState TypedDict
│   │   └── workflow.py           # LangGraph StateGraph & conditional routing
│   │
│   ├── mcp_server/
│   │   ├── server.py             # FastMCP server
│   │   └── tools/
│   │       ├── forecast.py       # get_forecast MCP tool
│   │       ├── rainfall.py       # get_rainfall_history MCP tool
│   │       └── soil_moisture.py  # get_soil_moisture MCP tool
│   │
│   ├── rag/
│   │   ├── documents/            # TNAU Agritech Guides (Paddy, Cotton, Banana, Groundnut)
│   │   ├── ingest.py             # Vector ingestion pipeline
│   │   └── retriever.py          # Citation-preserving vector retriever
│   │
│   ├── tools/
│   │   ├── geocoding.py          # LangChain Tool 1: Geocoding resolver
│   │   └── web_search.py         # LangChain Tool 2: Tavily search
│   │
│   ├── config.py                 # Configuration & environment variables
│   └── main.py                   # CLI entry point
│
├── frontend/
│   └── app.py                    # Interactive Streamlit Web UI
│
├── tests/
│   ├── test_mcp_tools.py         # MCP weather tools unit tests
│   ├── test_rag.py               # RAG ingestion & citation tests
│   └── test_workflow.py          # End-to-end multi-agent integration tests
│
├── .env.example
├── .gitignore
├── README.md
├── architecture.md
└── requirements.txt
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file from `.env.example`:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Run Tests
```powershell
# Test Weather MCP Tools
python -m pytest tests/test_mcp_tools.py -s

# Test RAG Ingestion & LangChain Tools
python -m pytest tests/test_rag.py -s

# Test End-to-End Multi-Agent Scenarios
python -m pytest tests/test_workflow.py -s
```

### 4. Run CLI Interface
```powershell
python backend/main.py "I grow paddy near Thanjavur. Should I irrigate this week?"
```

### 5. Launch Web UI
```powershell
streamlit run frontend/app.py
```

---

## 🌾 Example Questions Handled

1. **Irrigation Advisory:** *"I grow paddy near Thanjavur. Should I irrigate this week?"*
2. **Pest / Spray Safety:** *"Is it safe to spray pesticide on my cotton crop tomorrow in Coimbatore?"*
3. **Disaster Protection:** *"There is a cyclone warning. What should I do to protect my banana plantation in Cuddalore?"*
4. **Harvest Timing:** *"What is the best time to harvest groundnut in Madurai given this week's forecast?"*
5. **Missing Input Guardrail:** *"Should I spray chemicals today?"* (Prompts user for crop and location).
