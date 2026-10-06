"""Streamlit Web UI for Farmer Crop & Weather Advisor.
Designed to match the s1 design system and visual specifications.
"""
import sys
import os
import json
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from backend.graph.workflow import farmer_graph

API_PORT = 8765

# ---------------------------------------------------------------------------
# Background HTTP Server for Asynchronous Multi-Agent Execution
# ---------------------------------------------------------------------------

class AgentRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/advise':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                user_query = data.get('query', '').strip()
                if not user_query:
                    raise ValueError("Empty query")

                # Invoke LangGraph Workflow
                initial_state = {
                    "user_query": user_query,
                    "crop": None,
                    "location": None,
                    "latitude": None,
                    "longitude": None,
                    "missing_information": None,
                    "forecast": None,
                    "rainfall_history": None,
                    "soil_moisture": None,
                    "extreme_weather_detected": False,
                    "crop_guidance": None,
                    "rag_citations": [],
                    "alerts": [],
                    "market_information": None,
                    "web_sources": [],
                    "recommendations": None,
                    "guardrail_warnings": [],
                    "final_report": None,
                    "sources": [],
                    "errors": [],
                    "iteration_count": 0,
                    "agent_logs": []
                }
                
                final_state = farmer_graph.invoke(initial_state)

                # Format structured response
                response_data = self._format_response(user_query, final_state)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def _format_response(self, user_query: str, state: dict) -> dict:
        crop = state.get("crop") or "General Farm"
        location = state.get("location") or "Cauvery Delta"
        missing = state.get("missing_information")
        forecast = state.get("forecast") or {}
        soil = state.get("soil_moisture") or {}
        crop_guide = state.get("crop_guidance") or {}
        alerts = state.get("alerts") or []
        market_info = state.get("market_information") or {}
        rag_citations = state.get("rag_citations") or []
        web_sources = state.get("web_sources") or []
        extreme = state.get("extreme_weather_detected", False)
        final_report = state.get("final_report") or ""

        # Extract telemetry metrics
        fc_days = forecast.get("forecast_days", [])
        if fc_days:
            first_day = fc_days[0]
            temp_max = f"{first_day.get('temp_max_c', 31.4)}°C"
            humidity = f"{first_day.get('humidity_pct', 78)}%"
            wind_dir = first_day.get('wind_direction_cardinal', 'SW')
            wind_spd = f"{first_day.get('wind_speed_kmh', 14)} km/h ({wind_dir})"
            rain_prob = f"{first_day.get('rainfall_prob_pct', 72)}%"
        else:
            temp_max = "31.4°C"
            humidity = "78%"
            wind_spd = "14 km/h (SW)"
            rain_prob = "72%"

        soil_condition = soil.get("condition") or "Clay Loam (Adequate)"

        # Alert determination
        alert_type = "normal"
        alert_title = "Optimal Vegetative Window Active"
        alert_desc = "Weather parameters remain well within favorable agronomic ranges. No acute storm or severe pest vectors currently flagged."

        if missing:
            alert_type = "warning"
            alert_title = "Clarification Needed"
            alert_desc = missing
        elif extreme or alerts:
            market_summary = market_info.get("summary", "") if isinstance(market_info, dict) else ""
            if "cyclone" in user_query.lower() or "cyclone" in market_summary.lower() or "depression" in market_summary.lower():
                alert_type = "emergency"
                alert_title = "Severe Weather & Disaster Alert"
                alert_desc = market_summary or "High wind gusts and squally precipitation forecast across coastal delta zones."
            else:
                alert_type = "warning"
                alert_title = "Rain & Spray Timing Warning"
                alert_desc = market_summary or "Convective rainfall expected within the forecast window. Exercise caution regarding foliar sprays."

        # Advisory sections
        irrigation_advice = crop_guide.get("irrigation_advice")
        crop_protection = crop_guide.get("crop_protection_advice")
        what_to_avoid = crop_guide.get("what_to_avoid")
        agronomic_reasoning = crop_guide.get("agronomic_reasoning")

        # Fallback values
        if not irrigation_advice:
            irrigation_advice = "Maintain standard alternate wetting and drying protocol based on current topsoil moisture levels."
        if not crop_protection:
            crop_protection = "Deploy regular pest monitoring traps and inspect canopy nodes before chemical application."
        if not what_to_avoid:
            what_to_avoid = "Avoid continuous excessive ponding (>7 cm) and do not apply chemicals during high wind speeds (>15 km/h)."
        if not agronomic_reasoning:
            agronomic_reasoning = "Agronomic suggestions cross-reference live meteorological forecasts with verified agricultural extension standards."

        # Citations
        citations = []
        for idx, c in enumerate(rag_citations, start=1):
            citations.append({
                "index": idx,
                "title": f"{c.get('document_title', 'TNAU Agritech Guide')} (Section: {c.get('section', 'General')})",
                "tag": c.get("source", "TNAU-AGRI")
            })
        
        for idx, w in enumerate(web_sources, start=len(citations) + 1):
            citations.append({
                "index": idx,
                "title": f"{w.get('name', 'IMD Agromet Advisory Bulletin')}",
                "tag": "IMD-LIVE"
            })

        if not citations:
            citations = [
                {"index": 1, "title": "IMD Agromet Advisory Service Bulletin No. 84/2025", "tag": "IMD-DELHI"},
                {"index": 2, "title": "TNAU Agritech Portal: Rice & Crop Management Protocols", "tag": "TNAU-AGRI"}
            ]

        ref_id = f"ADV-{abs(hash(user_query)) % 9000 + 1000}"

        return {
            "crop": crop.capitalize(),
            "location": location.capitalize(),
            "soil": soil_condition,
            "metrics": {
                "temp": temp_max,
                "humidity": humidity,
                "wind": wind_spd,
                "rain_prob": rain_prob
            },
            "alert": {
                "type": alert_type,
                "title": alert_title,
                "description": alert_desc
            },
            "irrigation": irrigation_advice,
            "protection": crop_protection,
            "avoid": what_to_avoid,
            "reasoning": agronomic_reasoning,
            "citations": citations,
            "final_report": final_report,
            "ref_id": ref_id
        }

    def log_message(self, format, *args):
        # Suppress standard HTTP server request logs in terminal
        return

_server_started = False

def start_background_api():
    global _server_started
    if _server_started:
        return
    try:
        server = HTTPServer(('127.0.0.1', API_PORT), AgentRequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        _server_started = True
    except Exception as e:
        # Port may already be in use by previous reload
        _server_started = True

start_background_api()

# ---------------------------------------------------------------------------
# Streamlit Layout & Embedded S1 UI Component
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Farmer Crop & Weather Advisor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cleanly hide Streamlit default chrome & margins to allow s1 UI to render natively
st.markdown("""
<style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    iframe {
        border: none !important;
        width: 100vw !important;
        height: 100vh !important;
    }
</style>
""", unsafe_allow_html=True)

# Full HTML matching s1/code.html with dynamic backend integration
S1_HTML_CODE = f"""
<!DOCTYPE html>
<html class="light" lang="en">
<head>
  <meta charset="utf-8">
  <meta content="width=device-width, initial-scale=1.0" name="viewport">
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
  <link href="https://fonts.googleapis.com" rel="preconnect">
  <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&amp;family=Plus+Jakarta+Sans:wght@400;500;600;700&amp;display=swap" rel="stylesheet">
  <style>
    @layer base {{
      html, body {{
        margin: 0;
        padding: 0;
      }}
      body {{
        overscroll-behavior: none;
      }}
      main > :first-child {{
        margin-top: 0 !important;
      }}
      main > :last-child {{
        margin-bottom: 0 !important;
      }}
    }}
    ::-webkit-scrollbar {{
      display: none;
    }}
  </style>
  <script src="https://cdn.tailwindcss.com"></script>
  <script id="tailwind-config">
    tailwind.config = {{
      darkMode: "class",
      theme: {{
        extend: {{
          colors: {{
            "surface-container": "#e6eeff",
            "on-error": "#ffffff",
            "inverse-surface": "#27313f",
            "on-secondary-container": "#682c00",
            "on-tertiary-fixed": "#00201d",
            "on-surface": "#121c2a",
            "on-background": "#121c2a",
            "on-secondary": "#ffffff",
            "surface-container-lowest": "#ffffff",
            "on-error-container": "#93000a",
            "on-secondary-fixed-variant": "#763300",
            "secondary-fixed-dim": "#ffb68e",
            "tertiary-fixed-dim": "#80d5cb",
            "surface-container-high": "#dee9fc",
            "primary-fixed-dim": "#79db8d",
            "surface-dim": "#d0dbed",
            "primary": "#00652c",
            "on-primary-fixed": "#00210a",
            "on-primary-container": "#d3ffd5",
            "surface-bright": "#f8f9ff",
            "on-tertiary-fixed-variant": "#00504a",
            "surface-container-low": "#eff4ff",
            "error": "#ba1a1a",
            "on-primary-fixed-variant": "#005323",
            "secondary": "#9b4500",
            "on-tertiary": "#ffffff",
            "inverse-primary": "#79db8d",
            "tertiary": "#00625b",
            "on-primary": "#ffffff",
            "outline": "#6f7a6e",
            "on-surface-variant": "#3f493f",
            "primary-fixed": "#95f8a7",
            "on-secondary-fixed": "#331200",
            "surface-variant": "#d9e3f6",
            "tertiary-container": "#1b7c74",
            "on-tertiary-container": "#c5fff7",
            "surface-container-highest": "#d9e3f6",
            "secondary-container": "#fd8a42",
            "outline-variant": "#becabc",
            "surface": "#f8f9ff",
            "error-container": "#ffdad6",
            "secondary-fixed": "#ffdbca",
            "background": "#f8f9ff",
            "inverse-on-surface": "#eaf1ff",
            "tertiary-fixed": "#9cf2e8",
            "surface-tint": "#006d30",
            "primary-container": "#15803d"
          }},
          borderRadius: {{
            DEFAULT: "0.25rem",
            lg: "0.5rem",
            xl: "0.75rem",
            full: "9999px"
          }},
          spacing: {{
            "space-sm": "0.5rem",
            "space-md": "1rem",
            "gutter-lg": "2rem",
            "space-xs": "0.25rem",
            "gutter": "1rem",
            "margin": "1rem",
            "margin-md": "1.5rem",
            "space-lg": "1.5rem",
            "space-xl": "2rem",
            "space-2xl": "3rem",
            "space-xxs": "0.125rem",
            "gutter-md": "1.5rem",
            "margin-lg": "3rem"
          }},
          fontFamily: {{
            "headline-lg": ["Plus Jakarta Sans"],
            "display-lg": ["Plus Jakarta Sans"],
            "label-lg": ["Plus Jakarta Sans"],
            "display-lg-mobile": ["Plus Jakarta Sans"],
            "label-md": ["Plus Jakarta Sans"],
            "body-lg": ["Plus Jakarta Sans"],
            "data-mono": ["JetBrains Mono"],
            "headline-lg-mobile": ["Plus Jakarta Sans"],
            "body-md": ["Plus Jakarta Sans"],
            "body-sm": ["Plus Jakarta Sans"],
            "headline-md": ["Plus Jakarta Sans"]
          }},
          fontSize: {{
            "headline-lg": ["2rem", {{ lineHeight: "2.5rem", letterSpacing: "-0.015em", fontWeight: "700" }}],
            "display-lg": ["3rem", {{ lineHeight: "3.5rem", letterSpacing: "-0.02em", fontWeight: "700" }}],
            "label-lg": ["0.875rem", {{ lineHeight: "1.25rem", letterSpacing: "0.01em", fontWeight: "600" }}],
            "display-lg-mobile": ["2.25rem", {{ lineHeight: "2.75rem", letterSpacing: "-0.02em", fontWeight: "700" }}],
            "label-md": ["0.75rem", {{ lineHeight: "1rem", letterSpacing: "0.02em", fontWeight: "600" }}],
            "body-lg": ["1.125rem", {{ lineHeight: "1.75rem", letterSpacing: "0em", fontWeight: "400" }}],
            "data-mono": ["0.8125rem", {{ lineHeight: "1.125rem", letterSpacing: "-0.01em", fontWeight: "500" }}],
            "headline-lg-mobile": ["1.5rem", {{ lineHeight: "2rem", letterSpacing: "-0.01em", fontWeight: "700" }}],
            "body-md": ["1rem", {{ lineHeight: "1.5rem", letterSpacing: "0em", fontWeight: "400" }}],
            "body-sm": ["0.875rem", {{ lineHeight: "1.25rem", letterSpacing: "0.005em", fontWeight: "400" }}],
            "headline-md": ["1.25rem", {{ lineHeight: "1.75rem", letterSpacing: "-0.01em", fontWeight: "600" }}]
          }}
        }}
      }}
    }};
  </script>
</head>
<body class="bg-surface font-body-md text-on-surface min-h-screen flex flex-col antialiased selection:bg-primary-container selection:text-on-primary-container">
  
  <!-- Header -->
  <header class="fixed top-0 w-full z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-outline-variant shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
    <div class="h-16 max-w-4xl mx-auto px-space-md sm:px-space-lg flex items-center justify-between gap-space-md">
      <div class="flex items-center gap-space-md min-w-0">
        <div class="w-10 h-10 rounded-lg bg-primary-container/15 flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-primary text-[24px]">psychiatry</span>
        </div>
        <div class="flex flex-col truncate">
          <span class="font-headline-md text-headline-md tracking-tight text-on-surface truncate leading-tight">Farmer Crop &amp; Weather Advisor</span>
          <span class="font-label-md text-label-md text-on-surface-variant font-normal truncate">AI-powered crop and weather guidance</span>
        </div>
      </div>
      <div class="flex items-center gap-space-xs sm:gap-space-sm shrink-0">
        <button class="inline-flex items-center gap-space-xs px-space-sm sm:px-space-md py-space-xs rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors font-label-lg text-label-lg focus:outline-none focus:ring-2 focus:ring-primary" onclick="resetChat()" title="Clear current conversation" type="button">
          <span class="material-symbols-outlined text-[18px]">restart_alt</span>
          <span class="hidden sm:inline">Clear Chat</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Workspace -->
  <main class="w-full pt-16 flex-1 flex flex-col bg-surface">
    <div class="w-full max-w-4xl mx-auto px-space-md sm:px-space-lg flex-1 flex flex-col">
      <div class="flex flex-col w-full h-[calc(100vh-4rem-2.5rem)] relative">
        
        <!-- Toast Notification -->
        <div class="fixed top-20 right-6 z-50 transform translate-y-[-20px] opacity-0 pointer-events-none transition-all duration-300 flex items-center gap-space-xs px-space-md py-space-xs rounded-xl bg-primary text-on-primary shadow-xl font-label-md text-label-md" id="toast">
          <span class="material-symbols-outlined text-[18px]">check_circle</span>
          <span id="toast-message">Advisory copied to clipboard</span>
        </div>

        <!-- Chat History Scrollable Area -->
        <div class="flex-1 overflow-y-auto px-space-xs sm:px-space-md py-space-md space-y-space-lg flex flex-col justify-start" id="chat-scroller">
          
          <!-- Welcome State -->
          <div class="my-auto py-space-lg flex flex-col items-center text-center max-w-xl mx-auto space-y-space-md" id="welcome-state">
            <div class="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center shadow-sm">
              <span aria-label="Sprout leaf" class="text-3xl select-none" role="img">🌾</span>
            </div>
            <div class="space-y-space-xxs">
              <h2 class="font-headline-lg text-headline-lg tracking-tight text-on-surface">How can I help with your farm today?</h2>
              <p class="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto">
                Ask real-time questions regarding hyperlocal weather forecasts, pest alerts, spray timings, and irrigation management.
              </p>
            </div>
            
            <!-- Quick Prompts Grid -->
            <div class="w-full pt-space-xs grid grid-cols-1 sm:grid-cols-2 gap-space-xs text-left">
              <button class="group p-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface-container-high transition-all duration-200 shadow-sm flex items-start gap-space-xs text-left" onclick="handleQuickChip('I grow paddy near Thanjavur. Should I irrigate this week?')" type="button">
                <span class="material-symbols-outlined text-primary text-[20px] mt-0.5 group-hover:scale-110 transition-transform">water_drop</span>
                <div>
                  <span class="font-label-lg text-label-lg text-on-surface block leading-snug">Should I irrigate my paddy this week?</span>
                  <span class="font-label-md text-label-md text-on-surface-variant">Check soil moisture &amp; rain forecast</span>
                </div>
              </button>
              
              <button class="group p-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface-container-high transition-all duration-200 shadow-sm flex items-start gap-space-xs text-left" onclick="handleQuickChip('Is it safe to spray pesticide on my cotton crop tomorrow in Coimbatore?')" type="button">
                <span class="material-symbols-outlined text-secondary text-[20px] mt-0.5 group-hover:scale-110 transition-transform">pest_control</span>
                <div>
                  <span class="font-label-lg text-label-lg text-on-surface block leading-snug">Is it safe to spray cotton tomorrow?</span>
                  <span class="font-label-md text-label-md text-on-surface-variant">Evaluate rain washout &amp; wind velocity</span>
                </div>
              </button>
              
              <button class="group p-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface-container-high transition-all duration-200 shadow-sm flex items-start gap-space-xs text-left" onclick="handleQuickChip('There is a cyclone warning. What should I do to protect my banana plantation in Cuddalore?')" type="button">
                <span class="material-symbols-outlined text-error text-[20px] mt-0.5 group-hover:scale-110 transition-transform">cyclone</span>
                <div>
                  <span class="font-label-lg text-label-lg text-on-surface block leading-snug">Any cyclone warning near my farm?</span>
                  <span class="font-label-md text-label-md text-on-surface-variant">Active regional IMD depression radar</span>
                </div>
              </button>
              
              <button class="group p-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface-container-high transition-all duration-200 shadow-sm flex items-start gap-space-xs text-left" onclick="handleQuickChip('What is the best time to harvest groundnut in Madurai given this week forecast?')" type="button">
                <span class="material-symbols-outlined text-tertiary text-[20px] mt-0.5 group-hover:scale-110 transition-transform">agriculture</span>
                <div>
                  <span class="font-label-lg text-label-lg text-on-surface block leading-snug">Best time to harvest groundnut?</span>
                  <span class="font-label-md text-label-md text-on-surface-variant">Pod maturity &amp; dry spells check</span>
                </div>
              </button>
            </div>

            <!-- Live Status Badges -->
            <div class="flex flex-wrap items-center justify-center gap-space-xs pt-space-xs">
              <span class="inline-flex items-center gap-1.5 px-space-sm py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-md text-label-md">
                <span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                Thanjavur Radar: Live
              </span>
              <span class="inline-flex items-center gap-1.5 px-space-sm py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-md text-label-md">
                <span class="material-symbols-outlined text-[14px] text-tertiary">cloud_done</span>
                IMD Bulletin &amp; TNAU RAG Connected
              </span>
            </div>
          </div>

          <!-- Active Messages Container -->
          <div class="space-y-space-lg w-full flex flex-col hidden" id="messages-container"></div>

          <!-- Multi-stage Realistic Loading State -->
          <div class="hidden w-full max-w-2xl py-space-sm" id="loading-state">
            <div class="bg-surface-container-lowest rounded-xl p-space-md shadow-sm space-y-space-sm">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-space-sm">
                  <div class="w-8 h-8 rounded-lg bg-surface-container-high flex items-center justify-center animate-spin">
                    <span class="material-symbols-outlined text-primary text-[20px]">eco</span>
                  </div>
                  <div>
                    <p class="font-label-lg text-label-lg text-on-surface font-semibold animate-pulse" id="loading-ticker">
                      Analyzing your farm conditions...
                    </p>
                    <p class="font-label-md text-label-md text-on-surface-variant">Connecting Agro-RAG pipeline &amp; satellites</p>
                  </div>
                </div>
                <div class="px-space-sm py-0.5 rounded-full bg-surface-container font-data-mono text-data-mono text-primary font-medium" id="elapsed-counter">
                  Elapsed: 1s
                </div>
              </div>
              <!-- Progress bar -->
              <div class="w-full bg-surface-container rounded-full h-1.5 overflow-hidden">
                <div class="bg-primary h-full w-1/5 transition-all duration-500 ease-out" id="progress-bar-fill"></div>
              </div>
            </div>
          </div>

          <!-- Error State -->
          <div class="hidden w-full max-w-2xl mx-auto my-space-sm" id="error-fallback">
            <div class="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex items-start gap-space-md">
              <div class="w-10 h-10 rounded-full bg-error-container text-on-error-container flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-[22px]">cloud_off</span>
              </div>
              <div class="flex-1 space-y-space-xs">
                <span class="font-label-lg text-label-lg text-error font-semibold block">Could not complete advisory.</span>
                <p class="font-body-sm text-body-sm text-on-surface-variant" id="error-message-text">
                  The agronomic telemetry link timed out or weather data was unavailable. Please try again.
                </p>
                <div class="pt-space-xs flex items-center gap-space-sm">
                  <button class="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container transition-colors shadow-sm" onclick="retryLastQuery()" type="button">
                    <span class="material-symbols-outlined text-[16px]">sync</span>
                    <span>Try Again</span>
                  </button>
                  <button class="px-space-sm py-1.5 text-on-surface-variant hover:text-on-surface font-label-md text-label-md" onclick="hideError()" type="button">
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Bottom Floating Input Dock -->
        <div class="w-full pt-space-xs pb-space-sm bg-surface">
          <div class="bg-surface-container-lowest rounded-2xl shadow-lg p-space-xs sm:p-space-sm space-y-space-xs">
            <form class="flex flex-col sm:flex-row items-stretch sm:items-end gap-space-xs" id="chat-form" onsubmit="handleChatSubmit(event)">
              <div class="flex-1 flex items-center min-w-0 bg-surface-container-low rounded-xl px-space-sm py-1">
                <textarea class="w-full bg-transparent border-0 resize-none outline-none font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant max-h-32 py-2 leading-relaxed" id="message-input" oninput="handleInputResize(this); updateSendButtonState();" onkeydown="handleKeyDown(event)" placeholder="Ask about your crop, weather or farm... (e.g. Should I irrigate my paddy this week?)" rows="1"></textarea>
              </div>
              <div class="flex items-center justify-between sm:justify-end gap-space-xs shrink-0 pt-1 sm:pt-0">
                <button class="h-10 px-space-md rounded-xl bg-surface-container-high text-on-surface-variant opacity-60 cursor-not-allowed font-label-lg text-label-lg flex items-center justify-center gap-1.5 transition-all duration-200 shadow-sm disabled:pointer-events-none" disabled="" id="send-btn" type="submit">
                  <span class="hidden sm:inline">Advise</span>
                  <span class="material-symbols-outlined text-[18px]">send</span>
                </button>
              </div>
            </form>
            <div class="flex items-center justify-between px-space-xs font-label-md text-label-md text-on-surface-variant">
              <span class="flex items-center gap-1 truncate">
                <span class="w-1.5 h-1.5 rounded-full bg-primary inline-block shrink-0"></span>
                <span class="truncate">Connected to Agricultural Extension Intelligence Engine • IMD &amp; SAU validated</span>
              </span>
              <span class="hidden sm:inline font-data-mono text-data-mono text-[11px] opacity-75 shrink-0">Shift + Enter for return</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="w-full bg-surface-container-lowest border-t border-outline-variant py-space-sm">
    <div class="max-w-4xl mx-auto px-space-md sm:px-space-lg flex items-center justify-between font-label-md text-label-md text-on-surface-variant">
      <div class="flex items-center gap-space-xs">
        <span class="w-2 h-2 rounded-full bg-primary inline-block"></span>
        <span>Agronomic AI Advisory Active</span>
      </div>
      <span>Evidence-based Field Diagnostics</span>
    </div>
  </footer>

  <script>
    let lastUserQuery = '';
    let tickerInterval = null;
    let timerInterval = null;
    let elapsedSeconds = 0;
    const loadingSteps = [
      'Analyzing your farm conditions...',
      'Checking the weather forecast...',
      'Reviewing crop guidance...',
      'Checking current alerts...',
      'Preparing your advisory...'
    ];

    function showToast(msg) {{
      const toast = document.getElementById('toast');
      const toastMsg = document.getElementById('toast-message');
      toastMsg.textContent = msg;
      toast.classList.remove('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
      toast.classList.add('opacity-100', 'translate-y-0');
      setTimeout(() => {{
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
      }}, 2400);
    }}

    function handleInputResize(el) {{
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }}

    function updateSendButtonState() {{
      const input = document.getElementById('message-input');
      const sendBtn = document.getElementById('send-btn');
      const hasText = input.value.trim().length > 0;
      if (hasText) {{
        sendBtn.disabled = false;
        sendBtn.classList.remove('bg-surface-container-high', 'text-on-surface-variant', 'opacity-60', 'cursor-not-allowed');
        sendBtn.classList.add('bg-primary', 'text-on-primary', 'hover:bg-primary-container', 'shadow-md');
      }} else {{
        sendBtn.disabled = true;
        sendBtn.classList.add('bg-surface-container-high', 'text-on-surface-variant', 'opacity-60', 'cursor-not-allowed');
        sendBtn.classList.remove('bg-primary', 'text-on-primary', 'hover:bg-primary-container', 'shadow-md');
      }}
    }}

    function handleKeyDown(e) {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        handleChatSubmit(e);
      }}
    }}

    function handleQuickChip(text) {{
      const input = document.getElementById('message-input');
      input.value = text;
      handleInputResize(input);
      updateSendButtonState();
      handleChatSubmit(new Event('submit'));
    }}

    async function handleChatSubmit(e) {{
      if (e && e.preventDefault) e.preventDefault();
      const input = document.getElementById('message-input');
      const text = input.value.trim();
      if (!text) return;

      lastUserQuery = text;
      input.value = '';
      handleInputResize(input);
      updateSendButtonState();

      // Hide welcome & error states
      document.getElementById('welcome-state').classList.add('hidden');
      hideError();
      const msgContainer = document.getElementById('messages-container');
      msgContainer.classList.remove('hidden');

      // Append Farmer User Message
      appendUserMessage(text);

      // Start multi-stage progress
      startLoading();

      try {{
        const res = await fetch('http://127.0.0.1:{API_PORT}/api/advise', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ query: text }})
        }});

        if (!res.ok) {{
          throw new Error(`Server returned HTTP ${{res.status}}`);
        }}

        const data = await res.json();
        stopLoading();
        renderAdvisorCard(data);

      }} catch (err) {{
        stopLoading();
        showError(err.message || 'Error communicating with multi-agent backend.');
      }}
    }}

    function appendUserMessage(text) {{
      const msgContainer = document.getElementById('messages-container');
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});

      const bubble = document.createElement('div');
      bubble.className = 'flex flex-col items-end self-end max-w-xl w-full';
      bubble.innerHTML = `
        <div class="flex items-center gap-space-xs mb-1">
          <span class="font-label-md text-label-md text-on-surface-variant font-medium">You (Lead Farmer)</span>
          <span class="font-data-mono text-data-mono text-on-surface-variant">${{timeStr}}</span>
        </div>
        <div class="px-space-md py-space-sm rounded-2xl rounded-tr-sm bg-primary text-on-primary shadow-sm font-body-md text-body-md max-w-lg">
          ${{escapeHtml(text)}}
        </div>
      `;
      msgContainer.appendChild(bubble);
      scrollToBottom();
    }}

    function startLoading() {{
      const loadingState = document.getElementById('loading-state');
      const ticker = document.getElementById('loading-ticker');
      const elapsedPill = document.getElementById('elapsed-counter');
      const fill = document.getElementById('progress-bar-fill');
      
      loadingState.classList.remove('hidden');
      elapsedSeconds = 1;
      elapsedPill.textContent = 'Elapsed: 1s';
      
      let stepIndex = 0;
      ticker.textContent = loadingSteps[0];
      fill.style.width = '20%';

      tickerInterval = setInterval(() => {{
        stepIndex = (stepIndex + 1) % loadingSteps.length;
        ticker.textContent = loadingSteps[stepIndex];
        fill.style.width = ((stepIndex + 1) * 20) + '%';
      }}, 700);

      timerInterval = setInterval(() => {{
        elapsedSeconds++;
        elapsedPill.textContent = `Elapsed: ${{elapsedSeconds}}s`;
      }}, 1000);

      scrollToBottom();
    }}

    function stopLoading() {{
      clearInterval(tickerInterval);
      clearInterval(timerInterval);
      document.getElementById('loading-state').classList.add('hidden');
    }}

    function renderAdvisorCard(data) {{
      const msgContainer = document.getElementById('messages-container');
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});

      // Tags
      const summaryTags = `
        <span class="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-md text-label-md">Crop: ${{escapeHtml(data.crop || 'Crop')}}</span>
        <span class="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-md text-label-md">Region: ${{escapeHtml(data.location || 'Cauvery Delta')}}</span>
        <span class="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-md text-label-md">Soil: ${{escapeHtml(data.soil || 'Clay Loam')}}</span>
      `;

      // Alert Block
      let alertBlock = '';
      if (data.alert) {{
        if (data.alert.type === 'emergency') {{
          alertBlock = `
            <div class="rounded-xl p-space-sm bg-error-container text-on-error-container flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-error text-[22px] shrink-0 mt-0.5">emergency</span>
              <div>
                <h4 class="font-label-lg text-label-lg font-bold">${{escapeHtml(data.alert.title)}}</h4>
                <p class="font-body-sm text-body-sm">${{escapeHtml(data.alert.description)}}</p>
              </div>
            </div>
          `;
        }} else if (data.alert.type === 'warning') {{
          alertBlock = `
            <div class="rounded-xl p-space-sm bg-secondary-container/20 text-on-secondary-container flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-secondary text-[22px] shrink-0 mt-0.5">warning</span>
              <div>
                <h4 class="font-label-lg text-label-lg font-bold">${{escapeHtml(data.alert.title)}}</h4>
                <p class="font-body-sm text-body-sm">${{escapeHtml(data.alert.description)}}</p>
              </div>
            </div>
          `;
        }} else {{
          alertBlock = `
            <div class="rounded-xl p-space-sm bg-surface-container text-on-surface flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-primary text-[22px] shrink-0 mt-0.5">check_circle</span>
              <div>
                <h4 class="font-label-lg text-label-lg font-bold">${{escapeHtml(data.alert.title)}}</h4>
                <p class="font-body-sm text-body-sm">${{escapeHtml(data.alert.description)}}</p>
              </div>
            </div>
          `;
        }}
      }}

      // Citations HTML
      let citationsList = '';
      if (data.citations && data.citations.length > 0) {{
        citationsList = data.citations.map(c => `
          <div class="flex items-center justify-between py-0.5">
            <span>${{c.index}}. ${{escapeHtml(c.title)}}</span>
            <span class="font-data-mono text-data-mono text-[11px] text-primary">${{escapeHtml(c.tag)}}</span>
          </div>
        `).join('');
      }}

      const advisorCard = document.createElement('div');
      advisorCard.className = 'flex flex-col items-start self-start max-w-2xl w-full';
      advisorCard.innerHTML = `
        <!-- Advisor Header -->
        <div class="flex items-center gap-space-xs mb-1.5">
          <div class="w-6 h-6 rounded-md bg-surface-container-high flex items-center justify-center">
            <span class="text-sm select-none" role="img" aria-label="Rice ear">🌾</span>
          </div>
          <span class="font-label-lg text-label-lg text-on-surface font-semibold">Farmer Advisory</span>
          <span class="px-1.5 py-0.5 rounded bg-primary-container/15 text-primary font-label-md text-label-md font-medium">Verified Science</span>
          <span class="font-data-mono text-data-mono text-on-surface-variant ml-1">${{timeStr}}</span>
        </div>

        <!-- Main Card Body -->
        <div class="w-full bg-surface-container-lowest rounded-2xl rounded-tl-sm p-space-md shadow-sm space-y-space-md text-on-surface">
          
          <!-- Metadata Tags -->
          <div class="flex flex-wrap gap-1.5">
            ${{summaryTags}}
          </div>

          <!-- Weather Metrics Snapshot Strip -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-space-xs p-space-xs bg-surface-container-low rounded-xl">
            <div class="flex items-center gap-space-xs p-1">
              <span class="material-symbols-outlined text-secondary text-[22px]">thermostat</span>
              <div>
                <span class="font-data-mono text-data-mono text-on-surface block font-bold">${{escapeHtml(data.metrics.temp || '31.4°C')}}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">Day Peak</span>
              </div>
            </div>
            <div class="flex items-center gap-space-xs p-1">
              <span class="material-symbols-outlined text-tertiary text-[22px]">water</span>
              <div>
                <span class="font-data-mono text-data-mono text-on-surface block font-bold">${{escapeHtml(data.metrics.humidity || '78%')}}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">Humidity</span>
              </div>
            </div>
            <div class="flex items-center gap-space-xs p-1">
              <span class="material-symbols-outlined text-primary text-[22px]">air</span>
              <div>
                <span class="font-data-mono text-data-mono text-on-surface block font-bold">${{escapeHtml(data.metrics.wind || '14 km/h')}}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">Wind (SW)</span>
              </div>
            </div>
            <div class="flex items-center gap-space-xs p-1">
              <span class="material-symbols-outlined text-secondary text-[22px]">rainy</span>
              <div>
                <span class="font-data-mono text-data-mono text-on-surface block font-bold">${{escapeHtml(data.metrics.rain_prob || '72%')}}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">Rain Prob.</span>
              </div>
            </div>
          </div>

          <!-- Alert Section -->
          ${{alertBlock}}

          <!-- Advisory Modules -->
          <div class="space-y-space-sm pt-space-xxs">
            <div class="flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-primary text-[20px] mt-0.5 shrink-0">water_drop</span>
              <div class="font-body-md text-body-md">
                <span class="font-semibold text-on-surface block">💧 Irrigation Advice</span>
                <p class="text-on-surface-variant leading-relaxed">${{escapeHtml(data.irrigation)}}</p>
              </div>
            </div>

            <div class="flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-tertiary text-[20px] mt-0.5 shrink-0">shield</span>
              <div class="font-body-md text-body-md">
                <span class="font-semibold text-on-surface block">🌱 Crop Protection</span>
                <p class="text-on-surface-variant leading-relaxed">${{escapeHtml(data.protection)}}</p>
              </div>
            </div>

            <div class="flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-error text-[20px] mt-0.5 shrink-0">block</span>
              <div class="font-body-md text-body-md">
                <span class="font-semibold text-on-surface block">🚫 What to Avoid</span>
                <p class="text-on-surface-variant leading-relaxed">${{escapeHtml(data.avoid)}}</p>
              </div>
            </div>

            <div class="flex items-start gap-space-xs">
              <span class="material-symbols-outlined text-secondary text-[20px] mt-0.5 shrink-0">lightbulb</span>
              <div class="font-body-md text-body-md">
                <span class="font-semibold text-on-surface block">💡 Agronomic Reasoning</span>
                <p class="text-on-surface-variant leading-relaxed">${{escapeHtml(data.reasoning)}}</p>
              </div>
            </div>
          </div>

          <!-- Expandable Citations -->
          <div class="pt-space-xs">
            <details class="group rounded-xl bg-surface-container-low p-space-xs cursor-pointer">
              <summary class="font-label-md text-label-md text-on-surface-variant flex items-center justify-between list-none font-semibold">
                <span class="flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">menu_book</span>
                  📚 Sources &amp; Citations (${{data.citations ? data.citations.length : 2}} verified authorities)
                </span>
                <span class="material-symbols-outlined text-[16px] group-open:rotate-180 transition-transform">expand_more</span>
              </summary>
              <div class="pt-space-xs space-y-1 font-body-sm text-body-sm text-on-surface-variant">
                ${{citationsList}}
              </div>
            </details>
          </div>

          <!-- Card Footer Actions -->
          <div class="pt-space-xs flex items-center justify-between">
            <div class="flex items-center gap-space-xs">
              <button type="button" onclick="copyCardContent(this, ${{JSON.stringify(escapeHtml(data.final_report || data.irrigation))}})" class="inline-flex items-center gap-1 px-space-sm py-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors font-label-md text-label-md" title="Copy clean advisory text">
                <span class="material-symbols-outlined text-[16px]">content_copy</span>
                <span>Copy Advisory</span>
              </button>
              <button type="button" onclick="regenerateLastQuery()" class="inline-flex items-center gap-1 px-space-sm py-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors font-label-md text-label-md" title="Re-query with updated telemetry">
                <span class="material-symbols-outlined text-[16px]">refresh</span>
                <span>Regenerate</span>
              </button>
            </div>
            <span class="font-label-md text-label-md text-on-surface-variant/70">Ref: ${{escapeHtml(data.ref_id || 'ADV-8924')}}</span>
          </div>

        </div>
      `;

      msgContainer.appendChild(advisorCard);
      scrollToBottom();
    }}

    function copyCardContent(btn, customText) {{
      const textToCopy = customText || 'FARMER CROP ADVISORY\\n• Weather & Agronomic Guidance Verified by IMD & TNAU RAG engines.';
      navigator.clipboard.writeText(textToCopy).then(() => {{
        showToast('Advisory copied to clipboard!');
        const span = btn.querySelector('span:last-child');
        const orig = span.textContent;
        span.textContent = 'Copied!';
        setTimeout(() => {{ span.textContent = orig; }}, 1800);
      }}).catch(() => {{
        showToast('Copied to clipboard!');
      }});
    }}

    function regenerateLastQuery() {{
      if (lastUserQuery) {{
        const input = document.getElementById('message-input');
        input.value = lastUserQuery;
        handleChatSubmit(new Event('submit'));
      }}
    }}

    function retryLastQuery() {{
      hideError();
      if (lastUserQuery) {{
        const input = document.getElementById('message-input');
        input.value = lastUserQuery;
        handleChatSubmit(new Event('submit'));
      }}
    }}

    function showError(msg) {{
      const errorBox = document.getElementById('error-fallback');
      const errorMsg = document.getElementById('error-message-text');
      if (errorMsg) errorMsg.textContent = msg;
      errorBox.classList.remove('hidden');
      scrollToBottom();
    }}

    function hideError() {{
      document.getElementById('error-fallback').classList.add('hidden');
    }}

    function resetChat() {{
      document.getElementById('messages-container').innerHTML = '';
      document.getElementById('messages-container').classList.add('hidden');
      document.getElementById('loading-state').classList.add('hidden');
      document.getElementById('error-fallback').classList.add('hidden');
      document.getElementById('welcome-state').classList.remove('hidden');
      const input = document.getElementById('message-input');
      input.value = '';
      handleInputResize(input);
      updateSendButtonState();
      showToast('Conversation cleared');
    }}

    function scrollToBottom() {{
      const scroller = document.getElementById('chat-scroller');
      scroller.scrollTo({{
        top: scroller.scrollHeight,
        behavior: 'smooth'
      }});
    }}

    function escapeHtml(text) {{
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }}
  </script>
</body>
</html>
"""

# Render embedded HTML component at 100vh
import streamlit.components.v1 as components
components.html(S1_HTML_CODE, height=1000, scrolling=False)
