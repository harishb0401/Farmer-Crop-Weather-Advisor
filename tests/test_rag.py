"""Test suite for LangChain Tools and RAG retrieval with citations."""
import pytest
from backend.tools.geocoding import GeocodingTool
from backend.tools.web_search import TavilyAgriculturalSearchTool
from backend.rag.ingest import ingest_knowledge_base
from backend.rag.retriever import retrieve_agricultural_guidance


def test_geocoding_tool():
    """Verify Geocoding LangChain tool."""
    tool = GeocodingTool()
    res = tool.invoke({"location_name": "Madurai"})
    assert res["status"] == "success"
    assert res["found"] is True
    assert "latitude" in res
    print(f"\n[PASSED] Geocoding Tool resolved Madurai -> {res['display_name']}")


def test_tavily_search_tool():
    """Verify Tavily Search LangChain tool."""
    tool = TavilyAgriculturalSearchTool()
    res = tool.invoke({"query": "Tamil Nadu cyclone alert weather", "max_results": 2})
    assert res["status"] == "success"
    assert res["results_count"] > 0
    first = res["results"][0]
    assert "url" in first
    assert "title" in first
    print(f"\n[PASSED] Tavily Tool returned {res['results_count']} results for query. Top URL: {first['url']}")


def test_rag_ingest_and_paddy_query():
    """Verify RAG ingestion and retrieval for Paddy with citations."""
    ingest_knowledge_base()
    res = retrieve_agricultural_guidance(query="paddy irrigation stages and water depth", crop="paddy")
    assert res["status"] == "success"
    assert res["retrieved_count"] > 0
    assert len(res["citations"]) > 0
    first_citation = res["citations"][0]
    assert "TNAU" in first_citation["source"]
    assert "Paddy" in first_citation["document_title"]
    print(f"\n[PASSED] RAG retrieved Paddy guidance with citation: {first_citation['document_title']} ({first_citation['section']})")


def test_rag_banana_cyclone_query():
    """Verify RAG retrieval for Banana cyclone protection."""
    res = retrieve_agricultural_guidance(query="how to protect banana from cyclone high winds propping", crop="banana")
    assert res["status"] == "success"
    assert res["retrieved_count"] > 0
    first_citation = res["citations"][0]
    assert "Banana" in first_citation["document_title"]
    print(f"\n[PASSED] RAG retrieved Banana protection guide: {first_citation['document_title']}")


if __name__ == "__main__":
    print("Running LangChain Tools & RAG Tests...")
    test_geocoding_tool()
    test_tavily_search_tool()
    test_rag_ingest_and_paddy_query()
    test_rag_banana_cyclone_query()
    print("\n All LangChain Tools & RAG tests passed successfully!")
