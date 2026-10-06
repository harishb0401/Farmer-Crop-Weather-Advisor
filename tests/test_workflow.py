import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from backend.graph.workflow import farmer_graph


def test_scenario_1_paddy_irrigation():
    """Scenario 1: Paddy irrigation advice in Thanjavur."""
    state = farmer_graph.invoke({
        "user_query": "I grow paddy near Thanjavur. Should I irrigate this week?",
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
    })

    assert state["crop"] == "paddy"
    assert "thanjavur" in state["location"].lower()
    assert state["forecast"] is not None
    assert len(state["rag_citations"]) > 0
    assert "Irrigation" in state["final_report"] or "irrigation" in state["final_report"].lower()
    print("\n[PASSED] Scenario 1 (Paddy Irrigation) completed successfully.")


def test_scenario_2_missing_input_guardrail():
    """Scenario 2: Guardrail check on missing location and crop."""
    state = farmer_graph.invoke({
        "user_query": "Should I spray chemicals today?",
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
    })

    assert state["missing_information"] is not None
    assert "Farmer Advisory System Notice" in state["final_report"]
    print("\n[PASSED] Scenario 2 (Missing Input Guardrail) triggered clarification correctly.")


def test_scenario_3_banana_cyclone_routing():
    """Scenario 3: Cyclone protection for Banana triggers ReAct Alert Agent."""
    state = farmer_graph.invoke({
        "user_query": "There is a cyclone warning. What should I do to protect my banana plantation in Cuddalore?",
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
    })

    assert state["crop"] == "banana"
    assert state["extreme_weather_detected"] is True
    # ReAct agent must execute with hard iteration limit
    assert state["iteration_count"] > 0
    assert state["iteration_count"] <= 3
    assert len(state["rag_citations"]) > 0
    print(f"\n[PASSED] Scenario 3 (Banana Cyclone) routed through ReAct Alert Agent ({state['iteration_count']} iterations).")


if __name__ == "__main__":
    print("Running Workflow Integration Tests...")
    test_scenario_1_paddy_irrigation()
    test_scenario_2_missing_input_guardrail()
    test_scenario_3_banana_cyclone_routing()
    print("\n All workflow integration tests passed!")
