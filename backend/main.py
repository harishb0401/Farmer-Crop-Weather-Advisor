"""CLI Entry point for Farmer Crop & Weather Advisor."""
import sys
import os
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from backend.graph.workflow import farmer_graph
from backend.utils.timing import start_request_timer, stop_request_timer

console = Console(force_terminal=True)


def run_advisory(query: str):
    """Execute the multi-agent system on a farmer query."""
    console.print(Panel(f"[bold green]Farmer Query:[/bold green] {query}", title="🌾 Farmer Advisory Multi-Agent System"))
    
    start_time = start_request_timer()
    
    initial_state = {
        "user_query": query,
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

    stop_request_timer(start_time)

    # Print Agent Logs
    console.print("\n[bold yellow] Agent Execution Trace:[/bold yellow]")
    for log in final_state.get("agent_logs", []):
        console.print(f"  • [cyan]{log}[/cyan]")

    if final_state.get("errors"):
        console.print("\n[bold red] Non-fatal Warnings / Recovered Errors:[/bold red]")
        for err in final_state.get("errors", []):
            console.print(f"  - {err}")

    # Display Report
    console.print("\n" + "="*80 + "\n")
    report = final_state.get("final_report", "No report generated.")
    console.print(Markdown(report))
    console.print("\n" + "="*80 + "\n")
    return final_state


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "I grow paddy near Thanjavur. Should I irrigate this week?"
    run_advisory(query)
