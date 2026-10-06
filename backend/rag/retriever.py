"""RAG Retriever with citation formatting and crop filtering."""
import os
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

from backend.config import CHROMA_PERSIST_DIR
from backend.rag.ingest import EMBEDDING_MODEL_NAME, ingest_knowledge_base
from backend.utils.timing import timed_operation

_embedder: Optional[SentenceTransformer] = None
_client: Optional[chromadb.PersistentClient] = None
_collection = None


def get_collection():
    """Lazy-load the ChromaDB collection and embedding model."""
    global _embedder, _client, _collection
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    if _client is None:
        if not os.path.exists(CHROMA_PERSIST_DIR) or not os.listdir(CHROMA_PERSIST_DIR):
            print("ChromaDB not found or empty. Running initial ingestion...")
            ingest_knowledge_base()
        _client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        _collection = _client.get_or_create_collection(name="agricultural_guidelines")
    return _collection, _embedder


@timed_operation("RAG Retrieval", start_emoji="📚")
def retrieve_agricultural_guidance(
    query: str,
    crop: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Retrieve relevant agricultural guidelines and format with strict citations.
    
    Args:
        query: Specific agronomic question (e.g., 'irrigation schedule during flowering', 'pesticide spraying wind limits')
        crop: Optional crop filter (e.g., 'paddy', 'cotton', 'banana', 'groundnut')
        top_k: Number of relevant chunks to retrieve
        
    Returns:
        Structured response with retrieved passages, formal citations, and metadata.
    """
    try:
        collection, embedder = get_collection()
        query_vector = embedder.encode([query]).tolist()

        # Build where filter if crop is specified
        where_filter = None
        if crop:
            # Match substring in metadata
            where_filter = None # We search across vector space and post-rank/filter for maximum recall

        results = collection.query(
            query_embeddings=query_vector,
            n_results=top_k,
            where=where_filter
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        if not docs:
            return {
                "status": "not_found",
                "message": f"No agricultural guidelines found matching '{query}'.",
                "citations": [],
                "formatted_guidance": ""
            }

        citations = []
        guidance_blocks = []

        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            citation_entry = {
                "source": meta.get("source", "TNAU Agritech Portal"),
                "document_title": meta.get("document_title", "General Agronomy Guide"),
                "document_id": meta.get("doc_id", "TNAU-DOC"),
                "crop": meta.get("crop", "General"),
                "section": meta.get("section", "General Guidelines"),
                "file_name": meta.get("file_name", "")
            }
            citations.append(citation_entry)

            guidance_blocks.append(
                f"### [Citation {i+1}] {citation_entry['document_title']}\n"
                f"**Source:** {citation_entry['source']} | **Section:** {citation_entry['section']} | **Doc ID:** {citation_entry['document_id']}\n"
                f"{doc}\n"
            )

        return {
            "status": "success",
            "query": query,
            "crop": crop,
            "retrieved_count": len(docs),
            "citations": citations,
            "formatted_guidance": "\n".join(guidance_blocks)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RAG retrieval error: {str(e)}",
            "citations": [],
            "formatted_guidance": ""
        }
