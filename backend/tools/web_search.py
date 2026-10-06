"""LangChain Tool: Tavily Agricultural & Weather Alert Search."""
from typing import Optional, Dict, Any, Type, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from tavily import TavilyClient
from backend.config import TAVILY_API_KEY
from backend.utils.timing import timed_operation


class TavilySearchInput(BaseModel):
    query: str = Field(
        description="Search query targeting current weather alerts, cyclone warnings, flood warnings, heatwaves, or local crop mandi prices."
    )
    max_results: int = Field(
        default=3,
        description="Maximum number of search results to return (default: 3, max: 5)."
    )


class TavilyAgriculturalSearchTool(BaseTool):
    name: str = "tavily_agricultural_search"
    description: str = (
        "Searches the live web using Tavily for real-time agricultural alerts, cyclone warnings, "
        "flood/heatwave advisories, IMD (India Meteorological Department) bulletins, and recent mandi market price trends. "
        "Returns verified sources and clean content snippets."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    @timed_operation("Tavily Search", start_emoji="🔎")
    def _run(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Execute Tavily search query."""
        if not TAVILY_API_KEY:
            return {
                "status": "error",
                "message": "TAVILY_API_KEY is not configured in .env file."
            }

        try:
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=min(max_results, 5),
                include_answer=True
            )

            results: List[Dict[str, Any]] = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "score": r.get("score")
                })

            return {
                "status": "success",
                "query": query,
                "ai_summary": response.get("answer", ""),
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Tavily search failed: {str(e)}"
            }
