"""LangGraph Workflow definition for the Farmer Crop & Weather Advisor."""
from typing import Literal
from langgraph.graph import StateGraph, START, END

from backend.graph.state import FarmerAdvisorState
from backend.agents.supervisor import supervisor_node
from backend.agents.forecast_agent import forecast_node
from backend.agents.alert_agent import alert_node
from backend.agents.crop_advisor import crop_advisor_node
from backend.agents.report_writer import report_writer_node


def check_missing_info_router(state: FarmerAdvisorState) -> Literal["end", "forecast_agent"]:
    """Route to END if essential parameters are missing, otherwise proceed to Forecast."""
    if state.get("missing_information"):
        return "end"
    return "forecast_agent"


def weather_alert_router(state: FarmerAdvisorState) -> Literal["alert_agent", "crop_advisor"]:
    """
    Conditional routing:
    If extreme weather is detected or high risk is present, route to the ReAct Alert Agent.
    Otherwise, route directly to the Crop Advisor.
    """
    if state.get("extreme_weather_detected", False):
        return "alert_agent"
    return "crop_advisor"


def build_farmer_advisor_graph() -> StateGraph:
    """Construct and compile the LangGraph multi-agent advisory graph."""
    workflow = StateGraph(FarmerAdvisorState)

    # Add Agent Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("forecast_agent", forecast_node)
    workflow.add_node("alert_agent", alert_node)
    workflow.add_node("crop_advisor", crop_advisor_node)
    workflow.add_node("report_writer", report_writer_node)

    # Edge from START to Supervisor
    workflow.add_edge(START, "supervisor")

    # Conditional routing from Supervisor (Guardrail on missing info)
    workflow.add_conditional_edges(
        "supervisor",
        check_missing_info_router,
        {
            "end": END,
            "forecast_agent": "forecast_agent"
        }
    )

    # Conditional routing from Forecast Agent (Extreme weather / Alert need)
    workflow.add_conditional_edges(
        "forecast_agent",
        weather_alert_router,
        {
            "alert_agent": "alert_agent",
            "crop_advisor": "crop_advisor"
        }
    )

    # Alert Agent always passes gathered insights to Crop Advisor
    workflow.add_edge("alert_agent", "crop_advisor")

    # Crop Advisor proceeds to Report Writer
    workflow.add_edge("crop_advisor", "report_writer")

    # Report Writer finishes the workflow
    workflow.add_edge("report_writer", END)

    # Compile executable graph
    return workflow.compile()


# Singleton compiled graph instance
farmer_graph = build_farmer_advisor_graph()
