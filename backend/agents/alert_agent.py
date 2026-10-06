"""Alert Agent: ReAct agent with hard iteration limit using Tavily Web Search."""
import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from backend.graph.state import FarmerAdvisorState
from backend.agents.llm import get_llm, extract_text_content
from backend.tools.web_search import TavilyAgriculturalSearchTool
from backend.utils.timing import timed_operation

MAX_ITERATIONS = 3

REACT_PROMPT = """You are an Agricultural Disaster & Weather Alert ReAct Agent.
Your goal is to investigate current disaster warnings, cyclone alerts, IMD severe weather bulletins, and mandi/market price trends for a specific region and crop.

You have access to the Tavily search tool.
Use the following format strictly:

Thought: Consider what specific real-time information is needed (e.g. IMD cyclone alert, rainfall warnings, or mandi market rates).
Action: tavily_search: <search query string>
Observation: <result of search>
... (repeat Thought/Action/Observation at most {max_iterations} times)
Final Answer: Provide a structured summary of active weather alerts and relevant mandi prices with exact source URLs.

IMPORTANT RULES:
1. Do not exceed {max_iterations} search iterations.
2. Formulate focused queries like "IMD weather alert Thanjavur cyclone warning 2024" or "Paddy mandi price Thanjavur Tamil Nadu".
3. When you have sufficient evidence or reached the limit, output "Final Answer:".
"""


@timed_operation("Alert Agent", start_emoji="⏳")
def alert_node(state: FarmerAdvisorState) -> Dict[str, Any]:
    """Execute ReAct loop with hard iteration limit (MAX_ITERATIONS = 3)."""
    crop = state.get("crop", "crop")
    location = state.get("location", "region")
    user_query = state.get("user_query", "")
    
    llm = get_llm(temperature=0.1)
    search_tool = TavilyAgriculturalSearchTool()

    logs = [f"[Alert Agent ReAct] Starting alert investigation for {crop} in {location} (Limit: {MAX_ITERATIONS} iterations)"]
    errors = []
    web_sources = []
    alerts_found = []
    
    current_iteration = 0
    conversation_history = [
        SystemMessage(content=REACT_PROMPT.format(max_iterations=MAX_ITERATIONS)),
        HumanMessage(content=(
            f"Farmer Location: {location}\n"
            f"Crop: {crop}\n"
            f"Farmer Question: {user_query}\n"
            "Investigate if there are any active IMD weather warnings, cyclone alerts, flood advisories, or important mandi price notices."
        ))
    ]

    final_summary = ""

    while current_iteration < MAX_ITERATIONS:
        current_iteration += 1
        logs.append(f"[Alert Agent ReAct] --- Iteration {current_iteration}/{MAX_ITERATIONS} ---")
        
        try:
            response = llm.invoke(conversation_history)
            response_text = extract_text_content(response)
            logs.append(f"[Alert Agent ReAct Thinking] {response_text}")

            if "Final Answer:" in response_text or "final answer:" in response_text.lower():
                final_summary = response_text.split("Final Answer:")[-1].strip()
                break

            # Parse Action: tavily_search: <query>
            action_match = re.search(r"Action:\s*(?:tavily_search:)?\s*(.+)", response_text, re.IGNORECASE)
            if action_match:
                query_to_search = action_match.group(1).strip().strip('"').strip("'")
                logs.append(f"[Alert Agent Action] Tavily Search: '{query_to_search}'")

                tool_res = search_tool.invoke({"query": query_to_search, "max_results": 2})
                
                if tool_res.get("status") == "success":
                    results = tool_res.get("results", [])
                    obs_snippets = []
                    for r in results:
                        web_sources.append({
                            "type": "Live Web / Tavily Search",
                            "name": r.get("title", "Weather Alert"),
                            "url": r.get("url", ""),
                            "query": query_to_search
                        })
                        obs_snippets.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')[:300]}")
                        alerts_found.append({
                            "title": r.get("title"),
                            "url": r.get("url"),
                            "snippet": r.get("content")
                        })
                    observation = "\n---\n".join(obs_snippets) if obs_snippets else "No relevant articles found."
                else:
                    observation = f"Search failed: {tool_res.get('message')}"
                    errors.append(observation)

                logs.append(f"[Alert Agent Observation] Retrieved {len(results) if tool_res.get('status') == 'success' else 0} results.")
                
                # Append to conversation history for next ReAct step
                conversation_history.append(HumanMessage(content=f"Observation:\n{observation}\n\nNow provide your next Thought/Action or Final Answer."))
            else:
                # If model didn't provide action, treat response as final
                final_summary = response_text
                break

        except Exception as e:
            err_msg = f"Alert agent ReAct error on iteration {current_iteration}: {str(e)}"
            errors.append(err_msg)
            logs.append(f"[Alert Agent Error] {err_msg}")
            break

    # If reached max iteration limit without final answer, summarize gathered observations
    if not final_summary:
        logs.append(f"[Alert Agent ReAct] Reached MAX_ITERATIONS limit ({MAX_ITERATIONS}). Synthesizing collected evidence.")
        try:
            synth_resp = llm.invoke(conversation_history + [HumanMessage(content="You have reached the maximum iteration limit. Please provide your Final Answer based strictly on the observations gathered so far.")])
            final_summary = synth_resp.content.replace("Final Answer:", "").strip()
        except Exception:
            final_summary = "Live weather alerts search completed. Review verified web sources for latest advisories."

    logs.append(f"[Alert Agent] Completed in {current_iteration} iterations. Extracted {len(alerts_found)} alert items.")

    return {
        "alerts": alerts_found,
        "market_information": {"summary": final_summary},
        "web_sources": web_sources,
        "iteration_count": current_iteration,
        "agent_logs": logs,
        "errors": errors
    }
