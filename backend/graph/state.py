"""FarmerAdvisorState: Shared State for LangGraph Multi-Agent System."""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class FarmerAdvisorState(TypedDict):
    # User Input & Extracted Entities
    user_query: str
    crop: Optional[str]
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    
    # Missing information guardrail trigger
    missing_information: Optional[str]
    
    # Weather MCP Data
    forecast: Optional[Dict[str, Any]]
    rainfall_history: Optional[Dict[str, Any]]
    soil_moisture: Optional[Dict[str, Any]]
    extreme_weather_detected: bool
    
    # RAG Agricultural Guidance & Citations
    crop_guidance: Optional[Dict[str, Any]]
    rag_citations: List[Dict[str, Any]]
    
    # Live Alerts & Web Information (ReAct Alert Agent)
    alerts: List[Dict[str, Any]]
    market_information: Optional[Dict[str, Any]]
    web_sources: List[Dict[str, Any]]
    
    # Synthesis & Reasoning
    recommendations: Optional[Dict[str, Any]]
    guardrail_warnings: List[str]
    final_report: Optional[str]
    
    # Observability & Iteration Tracking
    sources: List[Dict[str, Any]]
    errors: Annotated[List[str], operator.add]
    iteration_count: int
    agent_logs: Annotated[List[str], operator.add]
