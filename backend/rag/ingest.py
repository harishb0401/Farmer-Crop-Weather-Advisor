"""RAG Document Ingestion into ChromaDB with citation metadata."""
import os
import glob
from pathlib import Path
from typing import List
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from backend.config import RAG_DOCS_DIR, CHROMA_PERSIST_DIR

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def load_and_chunk_documents() -> List[dict]:
    """Parse text documents from the documents directory into semantically meaningful chunks."""
    doc_files = glob.glob(str(RAG_DOCS_DIR / "*.txt"))
    chunks = []

    for file_path in doc_files:
        path_obj = Path(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse header lines for metadata
        lines = content.split("\n")
        title = path_obj.stem
        source = "TNAU Agritech Portal"
        doc_id = title
        crop = "General"

        for line in lines[:10]:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
            elif line.startswith("Source:"):
                source = line.replace("Source:", "").strip()
            elif line.startswith("Document ID:"):
                doc_id = line.replace("Document ID:", "").strip()
            elif line.startswith("Crop:"):
                crop = line.replace("Crop:", "").strip()

        # Split by section headers (##)
        raw_sections = content.split("\n## ")
        for idx, sec in enumerate(raw_sections):
            if not sec.strip():
                continue
            section_title = sec.split("\n")[0].strip() if idx > 0 else "Introduction & Metadata"
            full_section_text = f"Document: {title}\nCrop: {crop}\nSection: {section_title}\n\n{sec}"
            
            chunk_id = f"{doc_id}_sec_{idx}"
            chunks.append({
                "id": chunk_id,
                "text": full_section_text,
                "metadata": {
                    "document_title": title,
                    "source": source,
                    "doc_id": doc_id,
                    "crop": crop.lower(),
                    "section": section_title,
                    "file_name": path_obj.name
                }
            })

    return chunks


def ingest_knowledge_base():
    """Build or refresh the local Chroma vector store."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print("Reading and chunking agricultural guides...")
    chunks = load_and_chunk_documents()
    print(f"Generated {len(chunks)} document chunks.")

    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection = client.get_or_create_collection(name="agricultural_guidelines")

    # Clear existing documents to avoid duplicates
    existing = collection.get()
    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])
        print(f"Cleared {len(existing['ids'])} older chunks.")

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    embeddings = embedder.encode(texts).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f" Successfully ingested {len(chunks)} chunks into ChromaDB at {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    ingest_knowledge_base()
